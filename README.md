# IoTSeeker

forked from https://github.com/rapid7/IoTSeeker, to check if a device has default admin

## Install

pip3 install requests beautifulsoup4 html5lib beautifulsoup4

## usage

```
from iotScanner import verify
a = {"ip": "198.82.172.46", "port": "80"}
verify(a)
print(a)
```

**note that it only runs on windows due to slash problems, I will fix this later**

