# coding: utf-8

# In[1]:

#!/usr/bin/env python3


'ASR API'
__author__ = 'Charles Li'

import time
import random
import requests
import hmac
import base64
import urllib
#腾讯web API一句话识别请求
class tencentSpeech(object):
    __slots__ = 'SECRET_ID', 'SECRET_KEY', 'SourceType', 'URL', 'VoiceFormat'

    def __init__(self, SECRET_KEY, SECRET_ID):
        self.SECRET_KEY, self.SECRET_ID = SECRET_KEY, SECRET_ID
    @property
    def secret_id(self):
        return self.SECRET_ID
    @secret_id.setter
    def secret_id(self, SECRET_ID):
        if not isinstance(SECRET_ID, str):
            raise ValueError('SecretId must be a string!')
        if len(SecretId)==0:
            raise ValueError('SecretId can not be empty!')
        self.SECRET_ID = SECRET_ID
    @property
    def secret_key(self):
        return self.SECRET_KEY
    @secret_key.setter
    def secret_key(self, SECRET_KEY):
        if not isinstance(SECRET_KEY, str):
            raise ValueError('SecretKey must be a string!')
        if len(SECRET_KEY)==0:
            raise ValueError('SecretKey can not be empty!')
        self.SECRET_KEY = SECRET_KEY
    @property
    def source_type(self):
        return self.sourcetype
    @source_type.setter
    def source_type(self, SourceType):
        if not isinstance(SourceType, str):
            raise ValueError('SecretType must be an string!')
        if len(SourceType)==0:
            raise ValueError('SourceType can not be empty!')
        self.SourceType = SourceType
    @property
    def url(self):
        return self.URL
    @url.setter
    def url(self, URL):
        if not isinstance(URL, str):
            raise ValueError('url must be an string!')
        if len(URL)==0:
            raise ValueError('url can not be empty!')
        self.URL = URL
    @property
    def voiceformat(self):
        return self.VoiceFormat
    @voiceformat.setter
    def voiceformat(self, VoiceFormat):
        if not isinstance(VoiceFormat, str):
            raise ValueError('voiceformat must be an string!')
        if len(VoiceFormat)==0:
            raise ValueError('voiceformat can not be empty!')
        self.VoiceFormat = VoiceFormat
    def ASR(self, URL, voiceformat, sourcetype):
        self.url, self.voiceformat, self.source_type = URL, voiceformat, sourcetype
        return self.oneSentenceRecognition()
    def oneSentenceRecognition(self):
    	#拼接url和参数
        def formatSignString(config_dict):
            signstr="POSTaai.tencentcloudapi.com/?"
            argArr = []
            for a, b in config_dict:
                argArr.append(a + "=" + str(b))
            config_str = "&".join(argArr)
            return signstr + config_str
        #生成签名
        def encode_sign(signstr, SECRET_KEY):
            myhmac = hmac.new(SECRET_KEY.encode(), signstr.encode(), digestmod = 'sha1')
            code = myhmac.digest()
            #hmac() 完一定要decode()和 python 2 hmac不一样
            signature = base64.b64encode(code).decode()
            return signature
        #生成body
        def make_body(config_dict, sign_encode):
            ##注意URL编码的时候分str编码，整段编码会丢data
            body = ''
            for a, b in config_dict:
                body += urllib.parse.quote(a) + '=' + urllib.parse.quote(str(b)) + '&'
            return body + 'Signature=' + sign_encode
        HOST = 'aai.tencentcloudapi.com'
        config_dict= {
                        'Action'         : 'SentenceRecognition',
                        'Version'        : '2018-05-22',
                        'ProjectId'      : 0,
                        'SubServiceType' : 2,
                        'EngSerViceType' : '16k',
                        'VoiceFormat'    : self.VoiceFormat,
                        'UsrAudioKey'    : random.randint(0, 20),
                        'Timestamp'      : int(time.time()),
                        'Nonce'          : random.randint(100000, 200000),
                        'SecretId'       : self.SECRET_ID,
                        'Version'        : '2018-05-22',
                        'SourceType'     : self.SourceType
        }
        if self.SourceType == '0':
            config_dict['Url'] = urllib.parse.quote(str(self.url))
        else:
            #不能大于1M
            file_path = self.URL
            file = open(file_path, 'rb')
            content = file.read()
            config_dict['DataLen'] = len(content)
            config_dict['Data'] = base64.b64encode(content).decode()
            #config_dict['Data'] = content
            file.close()
        #按key排序
        config_dict = sorted(config_dict.items())
        signstr = formatSignString(config_dict)
        sign_encode = urllib.parse.quote(encode_sign(signstr, self.SECRET_KEY))
        body = make_body(config_dict, sign_encode)
        #Get URL
        req_url = "https://aai.tencentcloudapi.com"
        header = {
            'Host' : HOST,
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Charset' : 'UTF-8'
        }
        request = requests.post(req_url, headers = header, data = body)
        #有些音频utf8解码失败，存在编码错误
        s = request.content.decode("utf8","ignore")
        return s
