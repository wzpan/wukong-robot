# -*- coding:utf-8 -*-
from __future__ import print_function
import requests
import json
import logging

SLUG = "homeassistant"

def handle(text, mic, profile, wxbot=None):
    if "帮我" in text:
        input = text.replace("帮我", "")
    else:
        mic.say("开始家庭助手控制", cache=True)
        mic.say(u'请在滴一声后说明内容', cache=True)
        input = mic.activeListen(MUSIC=True)
    while not input:
        mic.say("请重新说", cache=True)
        input = mic.activeListen(MUSIC=True)
    input = input.split(",")[0].split("，")[0]
    hass(input, mic, profile)


def hass(text, mic, profile):
    if isinstance(text, bytes):
        text = text.decode('utf8')
    logger = logging.getLogger(__name__)
    if not profile[SLUG] or 'url' not in profile[SLUG] or \
       'port' not in profile[SLUG] or \
       'password' not in profile[SLUG]:
        mic.say("主人配置有误", cache=True)
        return
    url = profile[SLUG]['url']
    port = profile[SLUG]['port']
    password = profile[SLUG]['password']
    headers = {'x-ha-access': password, 'content-type': 'application/json'}
    r = requests.get(url + ":" + port + "/api/states", headers=headers)
    r_jsons = r.json()
    devices = []
    for r_json in r_jsons:
        entity_id = r_json['entity_id']
        domain = entity_id.split(".")[0]
        if domain not in ["group", "automation", "script"]:
            url_entity = url + ":" + port + "/api/states/" + entity_id
            entity = requests.get(url_entity, headers=headers).json()
            devices.append(entity)
    for device in devices:
        state = device["state"]
        attributes = device["attributes"]
        domain = device["entity_id"].split(".")[0]
        if 'dingdang' in attributes.keys():
            dingdang = attributes["dingdang"]
            if isinstance(dingdang, list):
                if text in dingdang:
                    try:
                        measurement = attributes["unit_of_measurement"]
                    except Exception as e:
                        pass
                    if 'measurement' in locals().keys():
                        text = text + "状态是" + state + measurement
                        mic.say(text, cache=True)
                    else:
                        text = text + "状态是" + state
                        mic.say(text, cache=True)
                    break
            elif isinstance(dingdang, dict):
                if text in dingdang.keys():
                    if isinstance(text, bytes):
                        text = text.decode('utf8')
                    try:
                        act = dingdang[text]
                        p = json.dumps({"entity_id": device["entity_id"]})
                        s = "/api/services/" + domain + "/"
                        url_s = url + ":" + port + s + act
                        request = requests.post(url_s, headers=headers, data=p)
                        if format(request.status_code) == "200" or \
                           format(request.status_code) == "201":
                            mic.say("执行成功", cache=True)
                        else:
                            mic.say("对不起,执行失败", cache=True)
                            print(format(request.status_code))
                    except Exception as e:
                        pass
                    break
    else:
        mic.say("对不起,指令不存在", cache=True)


def isValid(text):
    return any(word in text for word in ["开启家庭助手",
                                         "开启助手", "打开家庭助手", "打开助手",
                                         "家庭助手", "帮我"])
