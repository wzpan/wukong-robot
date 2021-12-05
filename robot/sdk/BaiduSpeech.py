# -*- coding:utf-8 -*-
import os
import json
import requests
import time
from robot import logging

logger = logging.getLogger(__name__)
TOKEN_PATH = os.path.expanduser("~/.wukong/.baiduSpeech_token")

# 百度语音识别 REST_API极速版
class baiduSpeech(object):
    def __init__(self, api_key, secret_key, dev_pid):
        self.api_key, self.secret_key, self.dev_pid = api_key, secret_key, dev_pid
        if not os.path.exists(TOKEN_PATH):
            self.token = self.fetch_token()
        else:
            self.token = self.load()

    def fetch_token(self):
        token_url = "http://openapi.baidu.com/oauth/2.0/token"
        body = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        try:
            req = requests.post(
                token_url,
                headers={"Content-Type": "application/json; charset=UTF-8"},
                data=body,
            )
            s = req.content.decode("utf-8", "ignore")
            result = json.loads(s)
            if "access_token" in result.keys() and "scope" in result.keys():
                if not "brain_enhanced_asr" in result["scope"].split(" "):
                    logger.error("当前百度云api_id尚未有语音识别的授权。")
                #### 请求access_token成功.
                with open(TOKEN_PATH, "w") as f:
                    result = {
                        key: result.get(key) for key in ["access_token", "expires_in"]
                    }
                    result["get_time"] = time.time()
                    data = json.dumps(result)
                    f.write(data)
                return result["access_token"]
        except Exception as err:
            logger.error("请求token_access失败: {}".format(err))

    def load(self):
        def is_json(f):
            try:
                json_object = json.load(f)
            except ValueError:
                return False
            return json_object

        try:
            with open(TOKEN_PATH, "r") as f:
                access_token = is_json(f)
                if not access_token:
                    return self.fetch_token()
                elif (
                    time.time() - access_token["expires_in"] - access_token["get_time"]
                    >= 0
                ):
                    return self.fetch_token()
                else:
                    return access_token["access_token"]
        except (OSError, KeyError, ValueError) as e:
            print("加载.baiduSpeech_token文件失败，请检查！原因是{}".format(e))

    def asr(self, pcm, file_type, sample_rate, dev_pid):
        asr_url = "http://vop.baidu.com/pro_api"
        length = len(pcm)
        if length == 0:
            logger.error("这个语音文件 {} 是空的".format(pcm))
        headers = {
            "Content-Type": "audio/" + file_type + ";rate=" + str(sample_rate),
            "Content-Length": str(length),
        }
        params = {"cuid": "wukong-Robot", "token": self.token, "dev_pid": self.dev_pid}

        try:
            req = requests.post(asr_url, params=params, headers=headers, data=pcm)
            s = req.content.decode("utf-8")
            return json.loads(s)
        except Exception as err:
            logger.error("百度ASR极速版请求失败: {}".format(err))
