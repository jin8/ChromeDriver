import csv
import json
import random
import sys

from selenium import webdriver

from process import *

quic = '--origin-to-force-quic-on="login.wikimedia.org:443,ssum.casalemedia.com:443,api.branch.io:443,partner.googleadservices.com:443,en.m.wikipedia.org:443,cm.g.doubleclick.net:443,www.amazon.com:443,a.thoughtleadr.com:443,www.google-analytics.com:443,aax-us-east.amazon-adsystem.com:443,ia.media-imdb.com:443,tpc.googlesyndication.com:443,m.imgur.com:443,sync.search.spotxchange.com:443,m.imdb.com:443,shopbop.sp1.convertro.com:443,fonts.googleapis.com:443,i.imgur.com:443,ib.adnxs.com:443,sb.scorecardresearch.com:443,www.googletagservices.com:443,tap.rubiconproject.com:443,sync.1rx.io:443,pixel.quantserve.com:443,ums.adtechus.com:443,api.imgur.com:443,sync.adaptv.advertising.com:443,s.amazon-adsystem.com:443,fls-na.amazon.com:443,sync.rhythmxchange.com:443,bh.contextweb.com:443,www.apple.com:443,www.burstnet.com:443,fonts.gstatic.com:443,geo-um.btrll.com:443,t4.liverail.com:443,s.media-imdb.com:443,image5.pubmatic.com:443,www.facebook.com:443,ads.yahoo.com:443,bnc.lt:443,images-na.ssl-images-amazon.com:443,upload.wikimedia.org:443,us-u.openx.net:443"'
h2 = "--disable-quic"
h1 = ""


def main(mode, iterations):
    ios6ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--enable-quic")
    chrome_options.add_argument("--user-agent=" + ios6ua)

    if sys.platform == "darwin":
        chrome_options.binary_location = "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
    elif sys.platform == 'linux2':
        chrome_options.binary_location = "/home/limjs/Downloads/google-chrome-unstable_current_amd64/opt/google/chrome-unstable/google-chrome-unstable"

    # chrome_options.add_argument("--disable-web-security")
    # chrome_options.add_argument("--enable-devtools-experiments")
    # driver = webdriver.Chrome(executable_path="driver/chromedriver",
    #                           desired_capabilities=capabilities,
    #                           chrome_options=chrome_options)

    if mode == "quic":
        m = quic
        chrome_options.add_argument(m)
    elif mode == "h2":
        m = h2
        chrome_options.add_argument(m)
    elif mode == "h1":
        m = h1
    else:
        print "Invalid mode. Exiting."
        sys.exit(-1)

    for i in range(int(iterations)):
        capabilities = {
            'loggingPrefs': {'browser':'ALL', 'driver':'ALL', 'performance': 'ALL'},
            # 'chromeOptions' : {
            #     'androidPackage': 'com.android.chrome',
            # }
        }

        f = open("sites.txt", "r")
        sites = f.read().strip().split("\n")
        random.shuffle(sites)

        for site in sites:
            driver = webdriver.Chrome(executable_path="driver/chromedriver",
                                  desired_capabilities=capabilities,
                                  chrome_options=chrome_options)
            driver.delete_all_cookies()
            driver.get(site)

            performance = driver.get_log('performance')
            track = {'site':site, 'Handshake Time':0,	'Page Load Time':0	,'DOM Load Time':0	,
                     '# Texts':0, '# JS/CSS':0, '# Images/Others':0, '# Domains':0,
                     'Encoded Data Size':0, 'Total Data Size':0}

            site_name = site.split(".")[1] + "_" + mode + "_" + str(i)

            with open('rawdata/' + site_name + '.csv', 'w') as csvfile:
                fieldnames = ["timestamp", "method", "requestId",
                              "url", "mimeType", "dataLength",
                              "encodedDataLength", "param-timestamp", "protocol"] #"frameId", "loadId", "requestId", #"status", "url","documentURL", "type"

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for entry in performance:
                    data = {"timestamp": "",
                            "method": "",
                            "requestId": "",
                            "url": "",
                            "mimeType": "",
                            "dataLength": "",
                            "encodedDataLength": "",
                            "param-timestamp": "",
                            "protocol": ""}
                            # "frameId":"",
                            # "loadId":"",
                            # "status":0,
                            # "documentURL":"",
                            # "type":"",

                    message = json.loads(entry['message'])
                    # print(str(message)+",")

                    inner_message = message['message']
                    # print(inner_message)

                    if(inner_message['method'] == 'Network.responseReceived'):
                        data["timestamp"] = entry["timestamp"]
                        data["method"] = inner_message["method"]
                        data["requestId"] = inner_message["params"]["requestId"]
                        data["mimeType"] = inner_message["params"]['response']['mimeType']
                        data["protocol"] = inner_message["params"]['response']["protocol"]
                        data["param-timestamp"] =  inner_message["params"]["timestamp"]

                        # rawdata["frameId"] = inner_message["params"]["frameId"]
                        # rawdata["loadId"] = inner_message["params"]["loaderId"]
                        # rawdata["status"] = inner_message["params"]['response']['status']
                        # rawdata["url"] = inner_message["params"]['response']['url']
                        # rawdata["type"] = inner_message["params"]['type']
                        # rawdata["encodedDataLength"] =inner_message["params"]['response']['encodedDataLength']

                        writer.writerow(data)

                    elif(inner_message['method']  == 'Network.loadingFinished'):
                        data["timestamp"] = entry["timestamp"]
                        data["method"] = inner_message["method"]
                        data["requestId"] = inner_message["params"]["requestId"]
                        data["param-timestamp"] = inner_message["params"]["timestamp"]
                        data['encodedDataLength'] = inner_message["params"]['encodedDataLength']

                        writer.writerow(data)

                    elif (inner_message['method'] == 'Page.loadEventFired'):
                        data["timestamp"] = entry["timestamp"]
                        data["method"] = inner_message["method"]
                        data["param-timestamp"] = inner_message["params"]["timestamp"]

                        writer.writerow(data)

                    elif (inner_message['method'] == "Page.domContentEventFired"):
                        data["timestamp"] = entry["timestamp"]
                        data["method"] = inner_message["method"]
                        data["param-timestamp"] = inner_message["params"]["timestamp"]

                        # rawdata["requestId"] = inner_message["params"]["requestId"]

                        writer.writerow(data)

                    elif(inner_message['method'] == "Network.requestWillBeSent"):
                        data["timestamp"] = entry["timestamp"]
                        data["method"] = inner_message['method']
                        data["requestId"] = inner_message["params"]["requestId"]

                        # rawdata["frameId"] = inner_message["params"]["frameId"]
                        # rawdata["loadId"] = inner_message["params"]["loaderId"]

                        # print(inner_message["params"]["request"]["url"])

                        try:
                            # print(inner_message["params"]["request"]["url"].split("//",1))
                            # print(inner_message["params"]["request"]["url"].split("//",1)[1].split("/",1)[0])
                            data["url"] = inner_message["params"]["request"]["url"].split("//",1)[1].split("/",1)[0]
                        except IndexError:
                            pass

                        data["param-timestamp"] = inner_message["params"]["timestamp"]

                        # rawdata["documentURL"] = inner_message["params"]["request"]['documentURL']
                        # rawdata['type'] = inner_message["params"]["request"]['type']

                        writer.writerow(data)

                    elif(inner_message['method']=="Network.dataReceived"):
                        data["timestamp"] = entry["timestamp"]
                        data["requestId"] = inner_message["params"]["requestId"]
                        data["method"] = inner_message["method"]
                        data['dataLength'] = inner_message["params"]['dataLength']
                        data['encodedDataLength'] = inner_message["params"]['encodedDataLength']
                        data["param-timestamp"] = inner_message["params"]["timestamp"]

                        writer.writerow(data)

            # for browser in driver.get_log('browser'):
            #     print(browser)

            driver.quit()

if __name__ == "__main__":
    main(mode=sys.argv[1], iterations=sys.argv[2])
    process(sys.argv[1])
