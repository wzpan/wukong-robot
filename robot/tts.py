from aip import AipSpeech
from .sdk import TencentSpeech
from . import utils
import logging
import tempfile
import base64
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BaiduTTS():
    """
    使用百度语音合成技术
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

    SLUG = "baidu-tts"

    def __init__(self, appid, api_key, secret_key, **args):
        super(self.__class__, self).__init__()
        self.client = AipSpeech(appid, api_key, secret_key)

    def get_speech(self, phrase):
        result  = self.client.synthesis(phrase, 'zh', 1, {
            'vol': 5,
        });
        # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
        if not isinstance(result, dict):
            tmpfile = utils.write_temp_file(data, '.mp3')
            logger.info('{} 语音合成成功，合成路径：{}'.format(self.SLUG, tmpfile))
            return tmpfile
        else:
            logger.critical('{} 合成失败！'.format(self.SLUG))


class TencentTTS():
    """
    腾讯的语音合成
    region: https://cloud.tencent.com/document/api/441/17365#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
    """

    SLUG = "tencent-tts"

    def __init__(self, appid, secretid, secret_key, **args):
        super(self.__class__, self).__init__()
        self.engine = TencentSpeech.tencentSpeech(secret_key, secretid)
                
    def get_speech(self, phrase):
        result = self.engine.TTS(phrase, 0, 1, 'ap-guangzhou')
        if 'Response' in result and 'Audio' in result['Response']:
            audio = result['Response']['Audio']
            data = base64.b64decode(audio)
            tmpfile = utils.write_temp_file(data, '.wav')
            logger.info('{} 语音合成成功，合成路径：{}'.format(self.SLUG, tmpfile))
            return tmpfile
        else:
            logger.critical('{} 合成失败！'.format(self.SLUG))
