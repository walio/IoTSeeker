# -*- coding:utf-8 -*-
import json
import requests
import logging
import re
from bs4 import BeautifulSoup
with open("./devices.cfg", "r") as f:
    dev_types = json.load(f)

dev_types = [[item, value] for item, value in enumerate(dev_types)]


def search4devtype(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp)

    for dev in dev_types:
        tomatch_locate = dev[1]["devTypePattern"][0]
        if tomatch_locate[0] == "header":
            tomatch = resp.headers[tomatch_locate[1]]
        elif tomatch_locate[0] == "body":
            if tomatch_locate[1] == "":
                tomatch = resp.text
            else:
                tomatch = soup.find(tomatch_locate[1])
        tomatch_pattern = dev[1]["devTypePattern"][1]
        if tomatch_pattern[0] == "==":
            if tomatch == tomatch_pattern[1]:
                return dev[0]
        elif tomatch_pattern[0].startswith("regex"):
            for _ in dev[1]["devTypePattern"][1][1:-1]:
                if not re.search(_, tomatch):
                    break
            else:
                return dev[0]
        elif tomatch_pattern[0] == "substr":
            if tomatch_pattern[1] in tomatch:
                return dev[0]
    return ""
