from aip import AipSpeech
from .sdk import TencentSpeech, AliSpeech
from . import utils
import logging
import requests
import base64
import urllib
import hmac
import hashlib
import time
import json

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaiduASR():
    """
    百度的语音识别API.
    dev_pid:
        - 1936: 普通话远场
        - 1536：普通话(支持简单的英文识别)
        - 1537：普通话(纯中文识别)
        - 1737：英语
        - 1637：粤语
        - 1837：四川话
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    填入 config.xml 中.
    ...
        baidu_yuyin: 
            appid: '9670645'
            api_key: 'qg4haN8b2bGvFtCbBGqhrmZy'
            secret_key: '585d4eccb50d306c401d7df138bb02e7'
        ...
    """

    SLUG = "baidu-asr"

    def __init__(self, appid, api_key, secret_key, dev_pid=1936, **args):
        super(self.__class__, self).__init__()
        self.client = AipSpeech(appid, api_key, secret_key)
        self.dev_pid = dev_pid

    def transcribe(self, fp):
        # 识别本地文件
        pcm = utils.get_pcm_from_wav(fp)
        res = self.client.asr(pcm, 'pcm', 16000, {
            'dev_pid': self.dev_pid,
        })
        if res['err_no'] == 0:
            logger.info('{} 语音识别到了：{}'.format(self.SLUG, res['result']))
            return ''.join(res['result'])
        else:
            logger.info('{} 语音识别出错了: {}'.format(self.SLUG, res['err_msg']))
            return ''


class TencentASR():
    """
    腾讯的语音识别API.
    """

    SLUG = "tencent-asr"

    def __init__(self, appid, secretid, secret_key, **args):
        super(self.__class__, self).__init__()
        self.engine = TencentSpeech.tencentSpeech(secret_key, secretid)        
                

    def transcribe(self, fp):
        mp3_path = utils.convert_wav_to_mp3(fp)
        r = self.engine.ASR(mp3_path, 'mp3', '1')
        utils.check_and_delete(mp3_path)
        res = json.loads(r)
        if 'Response' in res and 'Result' in res['Response']:
            logger.info('{} 语音识别到了：{}'.format(self.SLUG, res['Response']['Result']))
            return res['Response']['Result']
        else:
            logger.info('{} 语音识别出错了'.format(self.SLUG))
            return ''


class XunfeiASR():
    """
    科大讯飞的语音识别API.
    外网ip查询：https://ip.51240.com/
    """

    SLUG = "xunfei-asr"

    def __init__(self, appid, api_key):
        super(self.__class__, self).__init__()
        self.appid = appid
        self.api_key = api_key

    def getHeader(self, aue, engineType):
        curTime = str(int(time.time()))
        # curTime = '1526542623'
        param = "{\"aue\":\"" + aue + "\"" + ",\"engine_type\":\"" + engineType + "\"}"
        logger.debug("param:{}".format(param))
        paramBase64 = str(base64.b64encode(param.encode('utf-8')), 'utf-8')
        logger.debug("x_param:{}".format(paramBase64))

        m2 = hashlib.md5()
        m2.update((self.api_key + curTime + paramBase64).encode('utf-8'))
        checkSum = m2.hexdigest()
        header = {
            'X-CurTime': curTime,
            'X-Param': paramBase64,
            'X-Appid': self.appid,
            'X-CheckSum': checkSum,
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        }
        return header

    def getBody(self, filepath):
        binfile = open(filepath, 'rb')
        data = {'audio': base64.b64encode(binfile.read())}
        return data

    def transcribe(self, fp):
        URL = "http://api.xfyun.cn/v1/service/v1/iat"
        r = requests.post(URL, headers=self.getHeader('raw', 'sms16k'), data=self.getBody(fp))
        res = json.loads(r.content.decode('utf-8'))
        logger.info(res)
        if 'code' in res and res['code'] == '0':
            logger.info('{} 语音识别到了：{}'.format(self.SLUG, res['data']))
            return res['data']
        else:
            logger.info('{} 语音识别出错了'.format(self.SLUG))
            return ''


class AliASR():
    """
    阿里的语音识别API.
    """

    SLUG = "ali-asr"

    def __init__(self, appKey, token, **args):
        super(self.__class__, self).__init__()
        self.appKey, self.token = appKey, token        

    def transcribe(self, fp):
        result = AliSpeech.asr(self.appKey, self.token, fp)
        if result is not None:
            logger.info('{} 语音识别到了：{}'.format(self.SLUG, result))
            return result
        else:
            logger.info('{} 语音识别出错了'.format(self.SLUG))
            return ''
