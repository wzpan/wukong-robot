import logging
import sys
import os
from . import config, constants
from logging.handlers import HTTPHandler

def getLogger(name):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger(name)
    # StreamHandler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level=logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # FileHandler
    file_handler = logging.FileHandler(os.path.join(constants.TEMP_PATH, 'wukong.log'))
    file_handler.setLevel(level=logging.DEBUG)    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def readLog():
    log_path = os.path.join(constants.TEMP_PATH, 'wukong.log')
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            return f.read()
    return ''
