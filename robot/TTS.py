# -*- coding: utf -8-*-
import os
import base64
import tempfile
import pypinyin
from aip import AipSpeech
from . import utils, config, constants
from robot import logging
from pathlib import Path
from pypinyin import lazy_pinyin
from pydub import AudioSegment
from abc import ABCMeta, abstractmethod
from .sdk import TencentSpeech, AliSpeech, XunfeiSpeech, atc

logger = logging.getLogger(__name__)


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
                "{} 合成失败: 请先下载 syllables.zip (https://sourceforge.net/projects/hantts/files/?source=navbar) 并解压到 ~/.wukong 目录下".format(
                    self.SLUG
                )
            )
            return None
        logger.debug("{} 合成中...".format(self.SLUG))
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
        logger.info("{} 语音合成成功，合成路径：{}".format(self.SLUG, tmpfile))
        return tmpfile


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
            logger.info("{} 语音合成成功，合成路径：{}".format(self.SLUG, tmpfile))
            return tmpfile
        else:
            logger.critical("{} 合成失败！".format(self.SLUG), exc_info=True)


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
        **args
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
            logger.info("{} 语音合成成功，合成路径：{}".format(self.SLUG, tmpfile))
            return tmpfile
        else:
            logger.critical("{} 合成失败！".format(self.SLUG), exc_info=True)


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
        if tmpfile is not None:
            logger.info("{} 语音合成成功，合成路径：{}".format(self.SLUG, tmpfile))
            return tmpfile
        else:
            logger.critical("{} 合成失败！".format(self.SLUG), exc_info=True)


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
        raise ValueError("错误：找不到名为 {} 的 TTS 引擎".format(slug))
    else:
        if len(selected_engines) > 1:
            logger.warning("注意: 有多个 TTS 名称与指定的引擎名 {} 匹配").format(slug)
        engine = selected_engines[0]
        logger.info("使用 {} TTS 引擎".format(engine.SLUG))
        return engine.get_instance()


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
