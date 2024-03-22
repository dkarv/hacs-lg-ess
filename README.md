# hacs-lg-ess
HomeAssistant HACS integration for the LG ESS inverter.
Built with the Python library https://github.com/gluap/pyess (thanks!).

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dkarv&repository=hacs-lg-ess)



## Setup

The integration can be configured easily through the UI after getting the password. 


You need the local device password, __which is not the account password__. Instead there are a few ways to get it:

1. Get the mac address of the lg ess and convert it. Mac address AA:BB:CC:DD:11:22 -> password aabbccdd1122
2. Extract it using the pyess library (it has a cli) __while connected to the devices WiFi__.
3. Do a post request, e.g. with curl __while connected to the devices WiFi__:
```
curl --insecure -H "Charset:UTF-8" -H "Content-Type:application/json" https://10.10.1.98/v1/user/setting/read/password -d '{"key": "lgepmsuser!@#}'
```
