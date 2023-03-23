import websocket
import hashlib
import base64
import hmac
import json
import wave
import tempfile
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread

from robot import logging

logger = logging.getLogger(__name__)

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

asrWsParam = None
ttsWsParam = None

gResult = ""
gTTSResult = ""


class ASR_Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        # 控制台鉴权信息
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin"}

    # 生成url
    def create_url(self):
        url = "wss://ws-api.xfyun.cn/v2/iat"
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(
            self.APISecret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = (
            'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
            % (self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )
        # 将请求的鉴权参数组合为字典
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        # 拼接鉴权参数，生成url
        url = url + "?" + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        logger.debug("websocket url :", url)
        return url


class TTS_Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Text, voice_name="xiaoyan"):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {
            "aue": "raw",
            "auf": "audio/L16;rate=16000",
            "vcn": voice_name,
            "tte": "utf8",
        }
        self.Data = {
            "status": 2,
            "text": str(base64.b64encode(self.Text.encode("utf-8")), "UTF8"),
        }

    # 生成url
    def create_url(self):
        url = "wss://tts-api.xfyun.cn/v2/tts"
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(
            self.APISecret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = (
            'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
            % (self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )
        # 将请求的鉴权参数组合为字典
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        # 拼接鉴权参数，生成url
        url = url + "?" + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# ASR 收到websocket消息的处理
def asr_on_message(ws, message):
    global gResult
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            logger.critical(
                "xunfei-asr 识别出错了：sid:%s call error:%s code is:%s"
                % (sid, errMsg, code),
                stack_info=True,
            )
        else:
            data = json.loads(message)["data"]["result"]["ws"]
            result = ""
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            gResult = gResult + result
            logger.info(
                "sid:%s call success!,data is:%s"
                % (sid, json.dumps(data, ensure_ascii=False))
            )
    except Exception as e:
        logger.critical(f"xunfei-asr 识别出错了：{e}", stack_info=True)


# ASR 收到websocket错误的处理
def asr_on_error(ws, error):
    logger.error("xunfei-asr 识别出错：", error)


# ASR 收到websocket关闭的处理
def asr_on_close(ws, _foo, _bar):
    logger.debug("### closed ###")


# ASR 收到websocket连接建立的处理
def asr_on_open(ws):
    global asrWsParam

    def run(*args):
        frameSize = 1220  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
        with open(asrWsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if status == STATUS_FIRST_FRAME:

                    d = {
                        "common": asrWsParam.CommonArgs,
                        "business": asrWsParam.BusinessArgs,
                        "data": {
                            "status": 0,
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), "utf-8"),
                            "encoding": "raw",
                        },
                    }
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {
                        "data": {
                            "status": 1,
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), "utf-8"),
                            "encoding": "raw",
                        }
                    }
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {
                        "data": {
                            "status": 2,
                            "format": "audio/L16;rate=16000",
                            "audio": str(base64.b64encode(buf), "utf-8"),
                            "encoding": "raw",
                        }
                    }
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


# 收到websocket消息的处理
def tts_on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        audio = json.loads(message)["data"]["audio"]
        audio = base64.b64decode(audio)
        if code != 0:
            errMsg = json.loads(message)["message"]
            logger.error("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:
            with open(gTTSPath, "ab") as f:
                f.write(audio)
    except Exception as e:
        logger.error("receive msg,but parse exception:", e)


# 收到websocket错误的处理
def tts_on_error(ws, error):
    logger.error("xunfei-tts 合成出错：", error)


# 收到websocket关闭的处理
def tts_on_close(ws, _foo, _bar):
    global gTTSResult
    logger.debug("### closed ###")
    pcmdata = None
    try:
        with open(gTTSPath, "rb") as pcmfile:
            pcmdata = pcmfile.read()
        tmpfile = ""
        with tempfile.NamedTemporaryFile() as f:
            tmpfile = f.name
        with wave.open(tmpfile, "wb") as wavfile:
            wavfile.setparams((1, 2, 16000, 0, "NONE", "NONE"))
            wavfile.writeframes(pcmdata)
        gTTSResult = tmpfile
    except Exception as e:
        logger.error(f"XunfeiSpeech error: {e}", stack_info=True)


# 收到websocket连接建立的处理
def tts_on_open(ws):
    global ttsWsParam

    def run(*args):
        intervel = 2  # 等待结果间隔(单位:s)

        d = {
            "common": ttsWsParam.CommonArgs,
            "business": ttsWsParam.BusinessArgs,
            "data": ttsWsParam.Data,
        }
        d = json.dumps(d)
        ws.send(d)
        # sleep等待服务端返回结果
        time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


def transcribe(fpath, appid, api_key, api_secret):
    """
    科大讯飞ASR
    """
    global asrWsParam, gResult
    gResult = ""
    asrWsParam = ASR_Ws_Param(appid, api_key, APISecret=api_secret, AudioFile=fpath)
    websocket.enableTrace(False)
    wsUrl = asrWsParam.create_url()
    ws = websocket.WebSocketApp(
        wsUrl, on_message=asr_on_message, on_error=asr_on_error, on_close=asr_on_close
    )
    ws.on_open = asr_on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    return gResult


def synthesize(msg, appid, api_key, api_secret, voice_name="xiaoyan"):
    """
    科大讯飞TTS
    """
    global ttsWsParam, gTTSPath, gTTSResult
    with tempfile.NamedTemporaryFile() as f:
        gTTSPath = f.name
    ttsWsParam = TTS_Ws_Param(
        APPID=appid,
        APIKey=api_key,
        APISecret=api_secret,
        Text=msg,
        voice_name=voice_name,
    )
    websocket.enableTrace(False)
    wsUrl = ttsWsParam.create_url()
    ws = websocket.WebSocketApp(
        wsUrl, on_message=tts_on_message, on_error=tts_on_error, on_close=tts_on_close
    )
    ws.on_open = tts_on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    return gTTSResult
