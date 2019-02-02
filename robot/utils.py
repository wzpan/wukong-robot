import os
import tempfile
import wave
import struct

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

