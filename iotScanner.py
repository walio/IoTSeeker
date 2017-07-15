# -*- coding:utf-8 -*-
import json
import requests
import logging
import re
import base64
from bs4 import BeautifulSoup
with open("./devices.cfg", "r") as f:
    dev_types = json.load(f)
http_port = 80
logger = logging.getLogger(__name__)


def search_devtype(resp):
    soup = BeautifulSoup(resp.text.lower())

    for type_name, type_pattern in enumerate(dev_types):
        tomatch_locate = type_pattern["devTypePattern"][0]
        if tomatch_locate[0] == "header":
            tomatch = resp.headers[tomatch_locate[1]]
        elif tomatch_locate[0] == "body":
            if tomatch_locate[1] == "":
                tomatch = resp.text
            else:
                tomatch = soup.find(tomatch_locate[1])
        tomatch_pattern = type_pattern["devTypePattern"][1]
        if tomatch_pattern[0] == "==":
            if tomatch == tomatch_pattern[1]:
                return type_name
        elif tomatch_pattern[0].startswith("regex"):
            for _ in type_pattern["devTypePattern"][1][1:-1]:
                if not re.search(_, tomatch):
                    break
            else:
                return type_name
        elif tomatch_pattern[0] == "substr":
            if tomatch_pattern[1] in tomatch:
                return type_name
    return ""


def compose_url(dev_info):
    if not "url" in dev_info:
        dev_info["url"] = "http://%s/" % dev_info["ip_addr"]
    elif dev_info["url"].startswith("http"):
        pass
    elif dev_info["url"].startswith("/"):
        dev_info["url"] = "http://%s%s" % (dev_info["ip_addr"], dev_info["url"])

def check_login(dev_info):
    auth = dev_types[type_name]["auth"]
    logger.debug("checking login on %s\n" % url)
    if auth[0] == "basic":
        if not auth[1]:
            if requests.get(url).status_code == 200:
                logger.info("device %s is of type %s still has default password\n" % url, type_name)
                return dev_types
            else:
                logger.info("device %s of type %s has changed password\n" % url, type_name)
                return False
        if requests.get(url, headers={"Authorization": "Basic %s" % base64.b64encode(auth[1])}).status_code == 200:
            logger.info("device %s is of type %s still has default password\n" % url, type_name)
            return type_name
        else:
            logger.warning("device %s of type %s has changed password\n" % url, type_name)
            return False
    elif auth[0] == "form":
        if "extractFormData" in dev_types[type_name]:
            extracted_data = []
            for _ in dev_types[type_name]["extractFormData"]:
                extracted_data.append(re.search(_, resp.text).group())
        if auth[1].startswith("sub"):
            # substitude $1,$2,$3 and so on to %, and use dev_info["extractedData"] to assign
            post_data = re.sub("\$(\d+)", "%", auth[2]) % tuple(dev_info["extractedData"])
        if not auth[1]:
            resp_ = requests.get("%s?%s" % url, post_data)
            if auth[3] == "body":
                if auth[4] == "regex":
                    if re.search(auth[5], resp_.text):
                        logger.info("device %s is of type %s still has default password\n" % url, type_name)
                        return type_name
                    else:
                        logger.warning("device %s of type %s has changed password\n" % url, type_name)
                        return False
                elif auth[4] == "!substr":
                    if auth[5] in resp_.text:
                        logger.info("device %s is of type %s still has default password\n" % url, type_name)
                        return type_name
                    else:
                        logger.warning("device %s of type %s has changed password\n" % url, type_name)
                        return False
        logger.critical("auth[1] another type")
        return False
    elif auth[0] == "expect200":
        if resp.status_code == 200:
            logger.info("device %s is of type %s doesnot have any password\n" % url, type_name)

    if resp.status_code == 301 or resp.status_code == 302:



def check_init_login():
    pass


def check(ip_addr, stage):
    dev_info = {"ip_addr": ip_addr}
    compose_url(dev_info)
    if stage == "initialClickLoginPage":
        return check_init_login()
    dev_info["response"] = resp = requests.get(dev_info)
    soup = BeautifulSoup(resp.text.lower())
    logger.debug("got status=%d for $url\n" % resp.status_code)
    if resp.status_code == 301 or resp.status_code == 302:
        logger.debug("redirect should be automatically by requests but not. source ip:%s, destiny:%s\n" % url, resp.url)
    elif resp.status_code == 401:
        type_name = search_devtype(resp)
        if not type_name:
            return False
        logger.debug("device type is %s" % type_name)
        dev_info["type_name"] = type_name
        return dev_info if check_login({"url": resp.url, "response": resp, "type_name": type_name}) else False
    elif resp.status_code == 200:
        type_name = search_devtype(resp)
        if type_name:
            logger.debug("devType=%s\n" % type_name)
            dev_info["devType"] = type_name
            if "loginUrlPattern" in dev_types[type_name]:
                _ = re.search(dev_types[type_name]["loginUrlPattern"], resp.text)
                return check_login({"url": _.group(), "response": resp, "type_name": type_name}) if _ else False
            else:
                _ = dev_types[type_name]["nextUrl"]
                if _[0] == "string":
                    if not _[1]:
                        return check_login({"url": _[1], "response": resp, "type_name": type_name})
                    else:
                        return check_login({"url": resp.url, "response": resp, "type_name": type_name})
        elif stage == "look4LoginPage":
            pass
        elif not stage:
            meta_redirect_urls = soup.find_all("meta", {"class": "url"})
            if len(meta_redirect_urls) > 1:
                logger.debug("more than 1 meta redirect for ip %s" % url)
            elif len(meta_redirect_urls) == 1:
                return check(meta_redirect_urls[0], "look4LoginPage")
    elif resp.status_code == 404:
        logger.warning("canot find dev type for %s due to 404 response\n" % url)
        return False
    elif resp.status_code == 595:
        logger.warning("device %s: failed to establish TCP connection\n" % url)
        return False
    else:
        logger.warning("unexpected status code $status for ip %s\n" % url)
    if not search_devtype(resp):
        logger.warning("%s: didnot find dev type after trying all devices\n" % url)
        return False
