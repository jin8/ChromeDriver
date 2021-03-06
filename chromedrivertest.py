from selenium import webdriver
import time
import json
import csv

from selenium import webdriver
import selenium.webdriver.chrome.service as service


capabilities = {
    'loggingPrefs': {'browser':'ALL', 'driver':'ALL', 'performance': 'ALL'},
    'chromeOptions' : {
        #'chrome.switches': ["--incognito"],
        #'androidPackage': 'com.android.chrome',
        #'perfLoggingPrefs': {"traceCategories", "browser"}
    }
}
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
#chrome_options.add_argument("--disable-web-security")
#chrome_options.add_argument("–-enable-devtools-experiments")


driver = webdriver.Chrome(executable_path=r"C:\chromedriver_win32\chromedriver.exe",desired_capabilities=capabilities, chrome_options=chrome_options)


sites = ["https://google.com","https://youtube.com"]
for site in sites:
    driver.delete_all_cookies()
    driver.get(site)

    performance = driver.get_log('performance')
    track = {'site':site, 'Handshake Time':0,	'Page Load Time':0	,'DOM Load Time':0	,
             '# Texts':0, '# JS/CSS':0, '# Images/Others':0, '# Domains':0,
             'Encoded Data Size':0, 'Total Data Size':0}

    site_name = site.split(".")[0].split("//")[1]
    with open('performance'+'_'+site_name+'.csv', 'w',newline='') as csvfile:
        fieldnames = ["timestamp", "method", "requestId",  #"frameId", "loadId", "requestId", #"status", "url","documentURL", "type"
                      "url","mimeType", "dataLength", "encodedDataLength",
                      "param-timestamp", "protocol"]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in performance:
            data = {"timestamp":"",
                    "method":"",
                    #"frameId":"",
                    #"loadId":"",
                    "requestId":"",
                    #"status":0,
                    "url":"",
                    #"documentURL":"",
                    "mimeType":"",
                    #"type":"",
                    "dataLength":"",
                    "encodedDataLength":"",
                    "param-timestamp":"",
                    "protocol":""}


            message = json.loads(entry['message'])

            print(str(message)+",")
            inner_message = message['message']
            print(inner_message)
            if(inner_message['method'] == 'Network.responseReceived'):
                data["timestamp"] = entry["timestamp"]
                data["method"] = inner_message["method"]
                #rawdata["frameId"] = inner_message["params"]["frameId"]
                #rawdata["loadId"] = inner_message["params"]["loaderId"]
                data["requestId"] = inner_message["params"]["requestId"]

                #rawdata["status"] = inner_message["params"]['response']['status']
                #rawdata["url"] = inner_message["params"]['response']['url']
                data["mimeType"] = inner_message["params"]['response']['mimeType']
                data["protocol"] = inner_message["params"]['response']["protocol"]
                #rawdata["type"] = inner_message["params"]['type']
                #rawdata["encodedDataLength"] =inner_message["params"]['response']['encodedDataLength']
                data["param-timestamp"] =  inner_message["params"]["timestamp"]
                writer.writerow(data)

            elif(inner_message['method']  == 'Network.loadingFinished'):
                data["timestamp"] = entry["timestamp"]
                data["method"] = inner_message["method"]
                data["requestId"] = inner_message["params"]["requestId"]
                data["param-timestamp"] = inner_message["params"]["timestamp"]
                writer.writerow(data)


            elif (inner_message['method'] == 'Page.loadEventFired'):
                data["timestamp"] = entry["timestamp"]
                data["method"] = inner_message["method"]
                data["param-timestamp"] = inner_message["params"]["timestamp"]
                writer.writerow(data)
            elif (inner_message['method'] == "Page.domContentEventFired"):
                data["timestamp"] = entry["timestamp"]
                data["method"] = inner_message["method"]
                #rawdata["requestId"] = inner_message["params"]["requestId"]
                data["param-timestamp"] = inner_message["params"]["timestamp"]
                writer.writerow(data)
            elif(inner_message['method'] == "Network.requestWillBeSent"):

                data["timestamp"] = entry["timestamp"]
                data["method"] = inner_message['method']
                #rawdata["frameId"] = inner_message["params"]["frameId"]
                #rawdata["loadId"] = inner_message["params"]["loaderId"]
                data["requestId"] = inner_message["params"]["requestId"]
                print(inner_message["params"]["request"]["url"])
                try:
                    print(inner_message["params"]["request"]["url"].split("//",1))
                    print(inner_message["params"]["request"]["url"].split("//",1)[1].split("/",1)[0])
                    data["url"] = inner_message["params"]["request"]["url"].split("//",1)[1].split("/",1)[0]
                except IndexError:
                    pass

                #rawdata["documentURL"] = inner_message["params"]["request"]['documentURL']
                #rawdata['type'] = inner_message["params"]["request"]['type']
                data["param-timestamp"] = inner_message["params"]["timestamp"]
                writer.writerow(data)

            elif(inner_message['method']=="Network.dataReceived"):
                data["timestamp"] = entry["timestamp"]
                data["method"] = inner_message["method"]
                data['dataLength'] = inner_message["params"]['dataLength']
                data['encodedDataLength'] = inner_message["params"]['encodedDataLength']
                data["param-timestamp"] = inner_message["params"]["timestamp"]
                writer.writerow(data)
    for browser in driver.get_log('browser'):
        print(browser)
driver.quit()


'''
driver = webdriver.Remote('http://localhost:9515', capabilities)
driver.get('http://google.com')
driver.get('http://yahoo.com')
driver.get('http://daum.net')
driver.get('http://naver.com')
print(type(driver.get_log('performance')));
driver.quit()
'''