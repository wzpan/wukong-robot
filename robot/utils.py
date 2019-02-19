# -*- coding: utf-8-*-

import os
import tempfile
import wave
import struct
import shutil
import re
import time
import hashlib
from . import constants, config
from pydub import AudioSegment
from pytz import timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from robot import logging

logger = logging.getLogger(__name__)

do_not_bother = False

def sendEmail(SUBJECT, BODY, ATTACH_LIST, TO, FROM, SENDER,
              PASSWORD, SMTP_SERVER, SMTP_PORT):
    """
    发送邮件

    :param SUBJECT: 邮件标题
    :param BODY: 邮件正文
    :param ATTACH_LIST: 附件
    :param TO: 收件人
    :param FROM: 发件人
    :param SENDER: 发件人信息
    :param PASSWORD: 密码
    :param SMTP_SERVER: smtp 服务器
    :param SMTP_PORT: smtp 端口号
    :returns: True: 发送成功; False: 发送失败
    """
    txt = MIMEText(BODY.encode('utf-8'), 'html', 'utf-8')
    msg = MIMEMultipart()
    msg.attach(txt)    

    for attach in ATTACH_LIST:
        try:
            att = MIMEText(open(attach, 'rb').read(), 'base64', 'utf-8')
            filename = os.path.basename(attach)
            att["Content-Type"] = 'application/octet-stream'
            att["Content-Disposition"] = 'attachment; filename="%s"' % filename
            msg.attach(att)
        except Exception:
            logger.error(u'附件 %s 发送失败！' % attach)
            continue

    msg['From'] = SENDER
    msg['To'] = TO
    msg['Subject'] = SUBJECT

    try:
        session = smtplib.SMTP()
        session.connect(SMTP_SERVER, SMTP_PORT)
        session.starttls()
        session.login(FROM, PASSWORD)
        session.sendmail(SENDER, TO, msg.as_string())
        session.close()
        return True
    except Exception as e:
        logger.error(e)
        return False


def emailUser(SUBJECT="", BODY="", ATTACH_LIST=[]):
    """
    给用户发送邮件

    :param SUBJECT: subject line of the email
    :param BODY: body text of the email
    :returns: True: 发送成功; False: 发送失败
    """
    # add footer
    if BODY:
        BODY = u"%s，<br><br>这是您要的内容：<br>%s<br>" % (config['first_name'], BODY)

    recipient = config.get('/email/address', '')
    robot_name = config.get('robot_name_cn', 'wukong-robot')
    recipient = robot_name + " <%s>" % recipient
    user = config.get('/email/address', '')
    password = config.get('/email/password', '')
    server = config.get('/email/smtp_server', '')
    port = config.get('/email/smtp_port', '')

    if not recipient or not user or not password or not server or not port:
        return False
    try:
        sendEmail(SUBJECT, BODY, ATTACH_LIST, user, user,
                  recipient, password, server, port)
        return True
    except Exception as e:
        logger.error(e)
        return False


def get_file_content(filePath):
    """
    读取文件内容并返回

    :param filePath: 文件路径
    :returns: 文件内容
    :raises IOError: 读取失败则抛出 IOError
    """
    with open(filePath, 'rb') as fp:
        return fp.read()

def check_and_delete(fp):
    """ 
    检查并删除文件/文件夹

    :param fp: 文件路径
    """
    if isinstance(fp, str) and os.path.exists(fp):
        if os.path.isfile(fp):
            os.remove(fp)
        else:
            shutil.rmtree(fp)

def write_temp_file(data, suffix):
    """ 
    二进制形式写入临时文件

    :param data: 二进制数据
    :param suffix: 后缀名
    :returns: 文件保存后的路径
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        tmpfile = f.name
    return tmpfile

def get_pcm_from_wav(wav_path):
    """ 
    从 wav 文件中读取 pcm
    
    :param wav_path: wav 文件路径
    :returns: pcm 数据
    """
    wav = wave.open(wav_path, 'rb')
    return wav.readframes(wav.getnframes())

def convert_wav_to_mp3(wav_path):
    """ 
    将 wav 文件转成 mp3

    :param wav_path: wav 文件路径
    :returns: mp3 文件路径
    """
    if not os.path.exists(wav_path):
        logger.critical("文件错误 {}".format(wav_path))
        return None
    mp3_path = wav_path.replace('.wav', '.mp3')
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3")
    return mp3_path

def convert_mp3_to_wav(mp3_path):
    """ 
    将 mp3 文件转成 wav

    :param mp3_path: mp3 文件路径
    :returns: wav 文件路径
    """
    target = mp3_path.replace(".mp3", ".wav")
    if not os.path.exists(mp3_path):
        logger.critical("文件错误 {}".format(mp3_path))
        return None
    voice = AudioSegment.from_mp3(mp3_path).export(target, format="wav")
    return target        

def clean():
    """ 清理垃圾数据 """
    temp = constants.TEMP_PATH
    temp_files = os.listdir(temp)
    for f in temp_files:
        if os.path.isfile(os.path.join(temp, f)) and re.match(r'output[\d]*\.wav', os.path.basename(f)):
            os.remove(os.path.join(temp, f))

def is_proper_time():
    """ 是否合适时间 """
    if do_not_bother == True:
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
    return config.get('/do_not_bother/on_hotword', '悟空别吵.pmdl')

def get_do_not_bother_off_hotword():
    """ 关闭勿扰模式唤醒词 """
    return config.get('/do_not_bother/off_hotword', '悟空醒醒.pmdl')

def getTimezone():
    """ 获取时区 """
    return timezone(config.get('timezone', 'HKT'))

def getCache(msg):
    """ 获取缓存的语音 """
    md5 = hashlib.md5(msg.encode('utf-8')).hexdigest()
    mp3_cache = os.path.join(constants.TEMP_PATH, md5 + '.mp3')
    wav_cache = os.path.join(constants.TEMP_PATH, md5 + '.wav')
    if os.path.exists(mp3_cache):
        return mp3_cache
    elif os.path.exists(wav_cache):
        return wav_cache
    return None

def saveCache(voice, msg):
    """ 获取缓存的语音 """
    foo, ext = os.path.splitext(voice)
    md5 = hashlib.md5(msg.encode('utf-8')).hexdigest()
    shutil.copyfile(voice, os.path.join(constants.TEMP_PATH, md5+ext))
