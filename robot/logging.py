import logging
import os
from robot import constants
from logging.handlers import RotatingFileHandler

PAGE = 4096

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR

def tail(filepath, n=10):
    """
    实现 tail -n
    """
    res = ""
    with open(filepath, 'rb') as f:
        f_len = f.seek(0, 2)
        rem = f_len % PAGE
        page_n = f_len // PAGE
        r_len = rem if rem else PAGE
        while True:
            # 如果读取的页大小>=文件大小，直接读取数据输出
            if r_len >= f_len:
                f.seek(0)
                lines = f.readlines()[::-1]
                break

            f.seek(-r_len, 2)
            # print('f_len: {}, rem: {}, page_n: {}, r_len: {}'.format(f_len, rem, page_n, r_len))
            lines = f.readlines()[::-1]
            count = len(lines) -1   # 末行可能不完整，减一行，加大读取量

            if count >= n:  # 如果读取到的行数>=指定行数，则退出循环读取数据
                break
            else:   # 如果读取行数不够，载入更多的页大小读取数据
                r_len += PAGE
                page_n -= 1

    for line in lines[:n][::-1]:
        res += line.decode('utf-8')
    return res

def getLogger(name):
    """ 
    作用同标准模块 logging.getLogger(name) 
    
    :returns: logger
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s - %(funcName)s - line %(lineno)s - %(levelname)s - %(message)s')

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # FileHandler
    file_handler = RotatingFileHandler(os.path.join(constants.TEMP_PATH, 'wukong.log'), maxBytes=1024*1024,backupCount=5)
    file_handler.setLevel(level=logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def readLog(lines=200):
    """ 
    获取最新的指定行数的 log

    :param lines: 最大的行数
    :returns: 最新指定行数的 log
    """
    log_path = os.path.join(constants.TEMP_PATH, 'wukong.log')
    if os.path.exists(log_path):
        return tail(log_path, lines)
    return ''
    
