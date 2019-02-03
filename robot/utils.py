import os
import tempfile
import wave
import struct
import shutil
import re
import time
from . import constants, config
from pydub import AudioSegment

do_not_bother = False

def get_file_content(filePath):
    """ 读取文件 """
    with open(filePath, 'rb') as fp:
        return fp.read()

def check_and_delete(fp):
    """ 检查并删除文件 """
    if isinstance(fp, str) and os.path.exists(fp):
        os.remove(fp)

def write_temp_file(data, suffix):
    """ 二进制形式写入临时文件 """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        tmpfile = f.name
    return tmpfile

def get_pcm_from_wav(wav_path):
    """ 从 wav 文件中读取 pcm """
    wav = wave.open(wav_path, 'rb')
    return wav.readframes(wav.getnframes())

def convert_wav_to_mp3(wav_path):
    """ 将 wav 文件转成 mp3 """
    mp3_path = wav_path.replace('.wav', '.mp3')
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3")
    return mp3_path

def clean():
    """ 清理垃圾数据 """
    temp_files = os.listdir(constants.TEMP_PATH)
    for f in temp_files:
        if os.path.isfile(f) and re.match(r'output[\d]*\.wav', os.path.basename(f)):
            os.remove(f)

def is_proper_time():
    """ 是否合适时间 """
    if do_not_bother:
        return False
    if not config.has('do_not_bother'):
        return True
    bother_profile = config.get('do_not_bother')
    if not bother_profile['enable']:
        return True
    if 'since' not in bother_profile or 'till' not in bother_profile:
        return True
    since = bother_profile['since']
    till = bother_profile['till']
    current = time.localtime(time.time()).tm_hour
    if till > since:
        return current not in range(since, till)
    else:
        return not (current in range(since, 25) or
                    current in range(-1, till))

def get_do_not_bother_on_hotword():
    """ 打开勿扰模式唤醒词 """
    default_hotword = 'zhimaguanmen.pmdl'
    if not config.has('do_not_bother'):
        return default_hotword
    bother_profile = config.get('do_not_bother')
    return bother_profile.get('hotword', default_hotword)

def get_do_not_bother_off_hotword():
    """ 结束勿扰模式唤醒词 """
    default_hotword = 'zhimakaimen.pmdl'
    if not config.has('do_not_bother'):
        return default_hotword
    bother_profile = config.get('do_not_bother')
    return bother_profile.get('hotword', default_hotword)
