# encoding:utf-8
import urllib
import requests
import uuid
import json
import os
from robot import constants

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
    """ NLU 解析 """
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
    """ 提取意图 """
    if parsed is not None and 'result' in parsed and \
       'response_list' in parsed['result']:
        return parsed['result']['response_list'][0]['schema']['intent']
    else:
        return ''


def getSlots(parsed):
    """ 提取意图 """
    if parsed is not None and 'result' in parsed and \
       'response_list' in parsed['result']:
        return parsed['result']['response_list'][0]['schema']['slots']
    else:
        return []

def getSay(parsed):
    """ 提取意图 """
    if parsed is not None and 'result' in parsed and \
       'response_list' in parsed['result']:
        return parsed['result']['response_list'][0]['action_list'][0]['say']
    else:
        return []


if __name__ == '__main__':
    parsed = getUnit('今天的天气', "S13442", 'w5v7gUV3iPGsGntcM84PtOOM', 'KffXwW6E1alcGplcabcNs63Li6GvvnfL')
    print(parsed)
