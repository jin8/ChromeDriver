# CS442 Project
_Team Mobsters - Sungjin Hong, Jinmyeong Kwak and Jinsuk Lim_

Installation guide:  
OS: Ubuntu 14.04 LTS (64 bit)  

* Our proxy is designed in Google's Go programming language. Install Go by following the guideline here: https://golang.org/doc/install  
* Compile _proxy.go_ by running:  
`go install proxy.go`
* Run the output binary with the root privilege.  
* From a separate terminal, install Python's _Selenium_ library:  
`pip install selenium`
* Connect your mobile device to the desktop and go to *Settings > Tethering and Mobile Hotspot* and check *USB tethering*.  
* Disconnect from your desktop's default network to use the device's network. Our device, Nexus 5, has the additional option to set the preferred mode of networking (WiFi, LTE and 3G). If this is not your case, you may turn on the WiFi for a WiFi connection or turn it off for a LTE connection.  
* Run _wifi.sh, lte.sh_ or _3g.sh_ depending on your networking mode. Modify the ITERATIONS value in each script to your need. 
* The raw data should be generated in the respective directories _wifi, lte_ and _3g_. 
* Plots are generated in the  _plots_ directory (you need _R_ and _ggplot2_ package installed for this; refer to https://www.digitalocean.com/community/tutorials/how-to-set-up-r-on-ubuntu-14-04 and http://www.r-bloggers.com/installing-r-packages/ for the installation guide).  

Raw data and plots used for our experiment are stored in _DATA_ directory. Thank you!
