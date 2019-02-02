import os
import tempfile
import wave
import struct
from pydub import AudioSegment

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
