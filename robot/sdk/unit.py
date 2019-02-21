# encoding:utf-8
import urllib
import requests
import uuid
import json
import os
from dateutil import parser as dparser
from robot import constants, logging

logger = logging.getLogger(__name__)

def get_token(api_key, secret_key):
    cache = open(os.path.join(constants.TEMP_PATH, 'baidustt.ini'), 'a+')
    try:
        pms = cache.readlines()
        if len(pms) > 0:
            time = pms[0]
            tk = pms[1]
            # 计算token是否过期 官方说明一个月，这里保守29天
            time = dparser.parse(time)
            endtime = datetime.datetime.now()
            if (endtime - time).days <= 29:
                return tk
    finally:
        cache.close()
    URL = 'http://openapi.baidu.com/oauth/2.0/token'
    params = {'grant_type': 'client_credentials',
              'client_id': api_key,
              'client_secret': secret_key}
    r = requests.get(URL, params=params)
    try:
        r.raise_for_status()
        token = r.json()['access_token']
        return token
    except requests.exceptions.HTTPError:
        return ''

def getUnit(query, service_id, api_key, secret_key):
    """ 
    NLU 解析

    :param query: 用户的指令字符串
    :param service_id: UNIT 的 service_id
    :param api_key: UNIT apk_key
    :param secret_key: UNIT secret_key
    :returns: UNIT 解析结果。如果解析失败，返回 None
    """
    access_token = get_token(api_key, secret_key)
    url = 'https://aip.baidubce.com/rpc/2.0/unit/service/chat?access_token=' + access_token
    request={
        "query":query,
        "user_id":"888888",
    }
    body={
        "log_id": str(uuid.uuid1()),
        "version":"2.0",
        "service_id": service_id,
        "session_id": str(uuid.uuid1()),
        "request":request
    }
    try:
        headers = {'Content-Type': 'application/json'}
        request = requests.post(url, json=body, headers=headers)
        return json.loads(request.text)
    except Exception as e:
        return None


def getIntent(parsed):
    """ 
    提取意图

    :param parsed: UNIT 解析结果
    :returns: 意图数组
    """
    if parsed is not None and 'result' in parsed and \
       'response_list' in parsed['result']:
        return parsed['result']['response_list'][0]['schema']['intent']
    else:
        return ''


def hasIntent(parsed, intent):
    """ 
    判断是否包含某个意图

    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :returns: True: 包含; False: 不包含
    """
    if parsed is not None and 'result' in parsed and \
       'response_list' in parsed['result']:
        response_list = parsed['result']['response_list']
        for response in response_list:
            if response['schema']['intent'] == intent:
                return True
        return False
    else:
        return False


def getSlots(parsed, intent=''):
    """ 
    提取某个意图的所有词槽
    
    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :returns: 词槽列表。你可以通过 name 属性筛选词槽，
再通过 normalized_word 属性取出相应的值
    """
    if parsed is not None and 'result' in parsed and \
       'response_list' in parsed['result']:
        response_list = parsed['result']['response_list']
        if intent == '':
            return parsed['result']['response_list'][0]['schema']['slots']
        for response in response_list:
            if response['schema']['intent'] == intent:
                return response['schema']['slots']
    else:
        return []

def getSlotWords(parsed, intent, name):
    """ 
    找出命中某个词槽的内容
    
    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :param name: 词槽名
    :returns: 命中该词槽的值的列表。
    """
    slots = getSlots(parsed, intent)
    words = []
    for slot in slots:
        if slot['name'] == name:
            words.append(slot['normalized_word'])
    return words

def getSay(parsed, intent=''):
    """
    提取 UNIT 的回复文本

    :param parsed: UNIT 解析结果
    :param intent: 意图的名称
    :returns: UNIT 的回复文本
    """
    if parsed is not None and 'result' in parsed and \
       'response_list' in parsed['result']:
        response_list = parsed['result']['response_list']
        if intent == '':
            return response_list[0]['action_list'][0]['say']
        for response in response_list:
            if response['schema']['intent'] == intent:
                return response['action_list'][0]['say']
        return ''
    else:
        return ''


if __name__ == '__main__':
    parsed = getUnit('今天的天气', "S13442", 'w5v7gUV3iPGsGntcM84PtOOM', 'KffXwW6E1alcGplcabcNs63Li6GvvnfL')
    print(parsed)
