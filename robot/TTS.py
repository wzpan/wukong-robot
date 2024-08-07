# -*- coding: utf -8-*-
import os
import base64
import tempfile
import pypinyin
import subprocess
import uuid

import asyncio
import edge_tts
import nest_asyncio

from aip import AipSpeech
from . import utils, config, constants
from robot import logging
from pathlib import Path
from pypinyin import lazy_pinyin
from pydub import AudioSegment
from abc import ABCMeta, abstractmethod
from .sdk import TencentSpeech, AliSpeech, XunfeiSpeech, atc, VITSClient, VolcengineSpeech
import requests
from xml.etree import ElementTree

logger = logging.getLogger(__name__)
nest_asyncio.apply()

class AbstractTTS(object):
    """
    Generic parent class for all TTS engines
    """

    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    @abstractmethod
    def get_speech(self, phrase):
        pass


class HanTTS(AbstractTTS):
    """
    HanTTS：https://github.com/junzew/HanTTS
    要使用本模块, 需要先从 SourceForge 下载语音库 syllables.zip ：
    https://sourceforge.net/projects/hantts/files/?source=navbar
    并解压到 ~/.wukong 目录下
    """

    SLUG = "han-tts"
    CHUNK = 1024
    punctuation = [
        "，",
        "。",
        "？",
        "！",
        "“",
        "”",
        "；",
        "：",
        "（",
        "）",
        ":",
        ";",
        ",",
        ".",
        "?",
        "!",
        '"',
        "'",
        "(",
        ")",
    ]

    def __init__(self, voice="syllables", **args):
        super(self.__class__, self).__init__()
        self.voice = voice

    @classmethod
    def get_config(cls):
        # Try to get han-tts config from config
        return config.get("han-tts", {})

    def get_speech(self, phrase):
        """
        Synthesize .wav from text
        """
        src = os.path.join(constants.CONFIG_PATH, self.voice)
        text = phrase

        def preprocess(syllables):
            temp = []
            for syllable in syllables:
                for p in self.punctuation:
                    syllable = syllable.replace(p, "")
                if syllable.isdigit():
                    syllable = atc.num2chinese(syllable)
                    new_sounds = lazy_pinyin(syllable, style=pypinyin.TONE3)
                    for e in new_sounds:
                        temp.append(e)
                else:
                    temp.append(syllable)
            return temp

        if not os.path.exists(src):
            logger.error(
                f"{self.SLUG} 合成失败: 请先下载 syllables.zip (https://sourceforge.net/projects/hantts/files/?source=navbar) 并解压到 ~/.wukong 目录下",
                stack_info=True,
            )
            return None
        logger.debug(f"{self.SLUG} 合成中...")
        delay = 0
        increment = 355  # milliseconds
        pause = 500  # pause for punctuation
        syllables = lazy_pinyin(text, style=pypinyin.TONE3)
        syllables = preprocess(syllables)

        # initialize to be complete silence, each character takes up ~500ms
        result = AudioSegment.silent(duration=500 * len(text))
        for syllable in syllables:
            path = os.path.join(src, syllable + ".wav")
            sound_file = Path(path)
            # insert 500 ms silence for punctuation marks
            if syllable in self.punctuation:
                short_silence = AudioSegment.silent(duration=pause)
                result = result.overlay(short_silence, position=delay)
                delay += increment
                continue
            # skip sound file that doesn't exist
            if not sound_file.is_file():
                continue
            segment = AudioSegment.from_wav(path)
            result = result.overlay(segment, position=delay)
            delay += increment

        tmpfile = ""
        with tempfile.NamedTemporaryFile() as f:
            tmpfile = f.name
        result.export(tmpfile, format="wav")
        logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
        return tmpfile


class AzureTTS(AbstractTTS):
    """
    使用微软语音合成技术
    """

    SLUG = "azure-tts"

    def __init__(
        self, secret_key, region, lang="zh-CN", voice="zh-CN-XiaoxiaoNeural", **args
    ) -> None:
        super(self.__class__, self).__init__()
        self.post_url = "https://INSERT_REGION_HERE.tts.speech.microsoft.com/cognitiveservices/v1".replace(
            "INSERT_REGION_HERE", region
        )

        self.post_header = {
            "Ocp-Apim-Subscription-Key": secret_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
            "User-Agent": "curl",
        }
        self.sess = requests.session()
        body = ElementTree.Element("speak", version="1.0")
        body.set("xml:lang", "en-us")
        vc = ElementTree.SubElement(body, "voice")
        vc.set("xml:lang", lang)
        vc.set("name", voice)
        self.body = body
        self.vc = vc

    @classmethod
    def get_config(cls):
        # Try to get baidu_yuyin config from config
        return config.get("azure_yuyin", {})

    def get_speech(self, phrase):
        self.vc.text = phrase
        result = self.sess.post(
            self.post_url,
            headers=self.post_header,
            data=ElementTree.tostring(self.body),
        )
        # 识别正确返回语音二进制,http状态码为200
        if result.status_code == 200:
            tmpfile = utils.write_temp_file(result.content, ".mp3")
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        else:
            logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)


class BaiduTTS(AbstractTTS):
    """
    使用百度语音合成技术
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    填入 config.yml 中.
    ...
        baidu_yuyin:
            appid: '9670645'
            api_key: 'qg4haN8b2bGvFtCbBGqhrmZy'
            secret_key: '585d4eccb50d306c401d7df138bb02e7'
            dev_pid: 1936
            per: 1
            lan: 'zh'
        ...
    """

    SLUG = "baidu-tts"

    def __init__(self, appid, api_key, secret_key, per=1, lan="zh", **args):
        super(self.__class__, self).__init__()
        self.client = AipSpeech(appid, api_key, secret_key)
        self.per, self.lan = str(per), lan

    @classmethod
    def get_config(cls):
        # Try to get baidu_yuyin config from config
        return config.get("baidu_yuyin", {})

    def get_speech(self, phrase):
        result = self.client.synthesis(phrase, self.lan, 1, {"per": self.per})
        # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
        if not isinstance(result, dict):
            tmpfile = utils.write_temp_file(result, ".mp3")
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        else:
            logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)


class TencentTTS(AbstractTTS):
    """
    腾讯的语音合成
    region: 服务地域，挑个离自己最近的区域有助于提升速度。
        有效值：https://cloud.tencent.com/document/api/441/17365#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
    voiceType:
        - 0：女声1，亲和风格(默认)
        - 1：男声1，成熟风格
        - 2：男声2，成熟风格
    language:
        - 1: 中文，最大100个汉字（标点符号算一个汉子）
        - 2: 英文，最大支持400个字母（标点符号算一个字母）
    """

    SLUG = "tencent-tts"

    def __init__(
        self,
        appid,
        secretid,
        secret_key,
        region="ap-guangzhou",
        voiceType=0,
        language=1,
        **args,
    ):
        super(self.__class__, self).__init__()
        self.engine = TencentSpeech.tencentSpeech(secret_key, secretid)
        self.region, self.voiceType, self.language = region, voiceType, language

    @classmethod
    def get_config(cls):
        # Try to get tencent_yuyin config from config
        return config.get("tencent_yuyin", {})

    def get_speech(self, phrase):
        result = self.engine.TTS(phrase, self.voiceType, self.language, self.region)
        if "Response" in result and "Audio" in result["Response"]:
            audio = result["Response"]["Audio"]
            data = base64.b64decode(audio)
            tmpfile = utils.write_temp_file(data, ".wav")
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        else:
            logger.critical(f"{self.SLUG} 合成失败：{result}", stack_info=True)


class XunfeiTTS(AbstractTTS):
    """
    科大讯飞的语音识别API.
    """

    SLUG = "xunfei-tts"

    def __init__(self, appid, api_key, api_secret, voice="xiaoyan"):
        super(self.__class__, self).__init__()
        self.appid, self.api_key, self.api_secret, self.voice_name = (
            appid,
            api_key,
            api_secret,
            voice,
        )

    @classmethod
    def get_config(cls):
        # Try to get xunfei_yuyin config from config
        return config.get("xunfei_yuyin", {})

    def get_speech(self, phrase):
        return XunfeiSpeech.synthesize(
            phrase, self.appid, self.api_key, self.api_secret, self.voice_name
        )


class AliTTS(AbstractTTS):
    """
    阿里的TTS
    voice: 发音人，默认是 xiaoyun
        全部发音人列表：https://help.aliyun.com/document_detail/84435.html?spm=a2c4g.11186623.2.24.67ce5275q2RGsT
    """

    SLUG = "ali-tts"

    def __init__(self, appKey, token, voice="xiaoyun", **args):
        super(self.__class__, self).__init__()
        self.appKey, self.token, self.voice = appKey, token, voice

    @classmethod
    def get_config(cls):
        # Try to get ali_yuyin config from config
        return config.get("ali_yuyin", {})

    def get_speech(self, phrase):
        tmpfile = AliSpeech.tts(self.appKey, self.token, self.voice, phrase)
        if tmpfile:
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        else:
            logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)


class EdgeTTS(AbstractTTS):
    """
    edge-tts 引擎
    voice: 发音人，默认是 zh-CN-XiaoxiaoNeural
        全部发音人列表：命令行执行 edge-tts --list-voices 可以打印所有语音
    """

    SLUG = "edge-tts"

    def __init__(self, voice="zh-CN-XiaoxiaoNeural", **args):
        super(self.__class__, self).__init__()
        self.voice = voice

    @classmethod
    def get_config(cls):
        # Try to get ali_yuyin config from config
        return config.get("edge-tts", {})

    async def async_get_speech(self, phrase):
        try:
            tmpfile = os.path.join(constants.TEMP_PATH, uuid.uuid4().hex + ".mp3")
            tts = edge_tts.Communicate(text=phrase, voice=self.voice)
            await tts.save(tmpfile)    
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        except Exception as e:
            logger.critical(f"{self.SLUG} 合成失败：{str(e)}！", stack_info=True)
            return None

    def get_speech(self, phrase):
        event_loop = asyncio.new_event_loop()
        tmpfile = event_loop.run_until_complete(self.async_get_speech(phrase))
        event_loop.close()
        return tmpfile
        
            

class MacTTS(AbstractTTS):
    """
    macOS 系统自带的TTS
    voice: 发音人，默认是 Tingting
        全部发音人列表：命令行执行 say -v '?' 可以打印所有语音
        中文推荐 Tingting（普通话）或者 Sinji（粤语）
    """

    SLUG = "mac-tts"

    def __init__(self, voice="Tingting", **args):
        super(self.__class__, self).__init__()
        self.voice = voice

    @classmethod
    def get_config(cls):
        # Try to get ali_yuyin config from config
        return config.get("mac-tts", {})

    def get_speech(self, phrase):
        tmpfile = os.path.join(constants.TEMP_PATH, uuid.uuid4().hex + ".asiff")
        res = subprocess.run(
            ["say", "-v", self.voice, "-o", tmpfile, str(phrase)],
            shell=False,
            universal_newlines=True,
        )
        if res.returncode == 0:
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        else:
            logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)

class VITS(AbstractTTS):
    """
    VITS 语音合成
    需要自行搭建vits-simple-api服务器：https://github.com/Artrajz/vits-simple-api
    server_url : 服务器url，如http://127.0.0.1:23456
    api_key : 若服务器配置了API Key，在此填入
    speaker_id : 说话人ID，由所使用的模型决定
    length : 调节语音长度，相当于调节语速，该数值越大语速越慢。
    noise : 噪声
    noisew : 噪声偏差
    max : 分段阈值，按标点符号分段，加起来大于max时为一段文本。max<=0表示不分段。
    timeout: 响应超时时间，根据vits-simple-api服务器性能不同配置合理的超时时间。
    """

    SLUG = "VITS"

    def __init__(self, server_url, api_key, speaker_id, length, noise, noisew, max, timeout, **args):
        super(self.__class__, self).__init__()
        self.server_url, self.api_key, self.speaker_id, self.length, self.noise, self.noisew, self.max, self.timeout = (
            server_url, api_key, speaker_id, length, noise, noisew, max, timeout)

    @classmethod
    def get_config(cls):
        return config.get("VITS", {})

    def get_speech(self, phrase):
        result = VITSClient.tts(phrase, self.server_url, self.api_key, self.speaker_id, self.length, self.noise,
                                self.noisew, self.max, self.timeout)
        tmpfile = utils.write_temp_file(result, ".wav")
        logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
        return tmpfile

def get_engine_by_slug(slug=None):
    """
    Returns:
        A TTS Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """

    if not slug or type(slug) is not str:
        raise TypeError("无效的 TTS slug '%s'", slug)

    selected_engines = list(
        filter(
            lambda engine: hasattr(engine, "SLUG") and engine.SLUG == slug,
            get_engines(),
        )
    )

    if len(selected_engines) == 0:
        raise ValueError(f"错误：找不到名为 {slug} 的 TTS 引擎")
    else:
        if len(selected_engines) > 1:
            logger.warning(f"注意: 有多个 TTS 名称与指定的引擎名 {slug} 匹配")
        engine = selected_engines[0]
        logger.info(f"使用 {engine.SLUG} TTS 引擎")
        return engine.get_instance()

class VolcengineTTS(AbstractTTS):
    """
    VolcengineTTS 语音合成
    """

    SLUG = "volcengine-tts"

    def __init__(self, appid, token, cluster, voice_type, **args):
        super(self.__class__, self).__init__()
        self.engine = VolcengineSpeech.VolcengineTTS(appid=appid, token=token, cluster=cluster, voice_type=voice_type)

    @classmethod
    def get_config(cls):
        # Try to get ali_yuyin config from config
        return config.get("volcengine-tts", {})

    def get_speech(self, text):
        result = self.engine.execute(text)
        if result is None:
            logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)
        else:
            tmpfile = os.path.join(constants.TEMP_PATH, uuid.uuid4().hex + ".mp3")
            with open(tmpfile, "wb") as f:
                f.write(result)
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile

def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        engine
        for engine in list(get_subclasses(AbstractTTS))
        if hasattr(engine, "SLUG") and engine.SLUG
    ]
