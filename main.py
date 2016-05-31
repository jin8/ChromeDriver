import csv
import json
import random
import sys

from selenium import webdriver

from process import *

quic = ""
h2 = ""
h1 = ""


def main(mode, iterations):
    if mode == "quic":
        m = quic
    elif mode == "h2":
        m = h2
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
        ios6ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25"

        chrome_options = webdriver.ChromeOptions()
        # chrome_options.binary_location = "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--enable-quic")
        chrome_options.add_argument('--origin-to-force-quic-on="www.googletagmanager.com.this:443,s.ytimg.com.this:443,ssum.casalemedia.com.this:443,csc.beap.bc.yahoo.com.this:443,geo.yahoo.com.this:443,ecx.images-amazon.com.this:443,aax-us-east.amazon-adsystem.com.this:443,accounts.google.com.this:443,s.yimg.com.this:443,www.chinadaily.com.cn.this:443,d5nxst8fruw4z.cloudfront.net.this:443,b.scorecardresearch.com.this:443,bbs.chinadaily.com.cn.this:443,tap.rubiconproject.com.this:443,pix04.revsci.net.this:443,ums.adtechus.com.this:443,b.thumbs.redditmedia.com.this:443,www.yahoo.com.this:443,fls-na.amazon.com.this:443,www.googletagservices.com.this:443,bh.contextweb.com.this:443,adpic.chinadaily.com.cn.this:443,partner.googleadservices.com.this:443,www.google.com.this:443,ads.yahoo.com.this:443,api.imgur.com.this:443,pr-bh.ybp.yahoo.com.this:443,us-u.openx.net.this:443,www.redditmedia.com.this:443,pixel.redditmedia.com.this:443,pixel.quantserve.com.this:443,www.amazon.com.this:443,cloudfront-labs.amazonaws.com.this:443,www.redditstatic.com.this:443,ia.media-imdb.com.this:443,tpc.googlesyndication.com.this:443,www.google.co.kr.this:443,m.imdb.com.this:443,sb.scorecardresearch.com.this:443,googleads.g.doubleclick.net.this:443,c.cnzz.com.this:443,gzs20.cnzz.com.this:443,www.youtube.com.this:443,ssl.gstatic.com.this:443,geo.query.yahoo.com.this:443,sync.rhythmxchange.com.this:443,a25efb2941951158266fb235777d53410.profile.nrt53.cloudfront.net.this:443,www.burstnet.com.this:443,t4.liverail.com.this:443,image5.pubmatic.com.this:443,www.google-analytics.com.this:443,syndication.twitter.com.this:443,upload.wikimedia.org.this:443,en.m.wikipedia.org.this:443,cm.g.doubleclick.net.this:443,d31qbv1cthcecs.cloudfront.net.this:443,m.imgur.com.this:443,bnc.lt.this:443,en.wikipedia.org.this:443,same.chinadaily.com.cn.this:443,shopbop.sp1.convertro.com.this:443,i.imgur.com.this:443,s13.cnzz.com.this:443,m.youtube.com.this:443,s.amazon-adsystem.com.this:443,www.apple.com.this:443,images.apple.com.this:443,a.thoughtleadr.com.this:443,rtd.tubemogul.com.this:443,pbs.twimg.com.this:443,s.media-imdb.com.this:443,sync.adaptv.advertising.com.this:443,g-ecx.images-amazon.com.this:443,www.facebook.com.this:443,s.zkcdn.net.this:443,match.adsrvr.org.this:443,pubads.g.doubleclick.net.this:443,api.branch.io.this:443,www.reddit.com.this:443,metrics.apple.com.this:443,sync.search.spotxchange.com.this:443,mobile.twitter.com.this:443,fonts.googleapis.com.this:443,ib.adnxs.com.this:443,ma.twimg.com.this:443,engine.a.redditmedia.com.this:443,sync.1rx.io.this:443,z-ecx.images-amazon.com.this:443,reddit.com.this:443,www.gstatic.com.this:443,events.redditmedia.com.this:443,c.wrating.com.this:443,fonts.gstatic.com.this:443,geo-um.btrll.com.this:443,a.thumbs.redditmedia.com.this:443,cl2.webterren.com.this:443,ssl.google-analytics.com.this:443,images-na.ssl-images-amazon.com.this:443"')
        chrome_options.add_argument("--user-agent=" + ios6ua)
        # chrome_options.add_argument(m)
        # chrome_options.add_argument("--disable-web-security")
        # chrome_options.add_argument("--enable-devtools-experiments")
        # driver = webdriver.Chrome(executable_path="driver/chromedriver",
        #                           desired_capabilities=capabilities,
        #                           chrome_options=chrome_options)

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
                    print(str(message)+",")

                    inner_message = message['message']
                    print(inner_message)

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
    process()
