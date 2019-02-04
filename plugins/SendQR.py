# -*- coding: utf-8-*-

import os
import sys
from robot import constants

SLUG = "sendqr"

def handle(text, mic, profile, wxbot=None):
    """
        Reports the current time based on the user's timezone.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxbot -- wechat bot instance
    """
    if 'wechat' not in profile or not profile['wechat'] or wxbot is None:
        mic.say(u'请先在配置文件中开启微信接入功能', cache=True)
        return
    if 'email' not in profile or ('enable' in profile['email']
                                  and not profile['email']):
        mic.say(u'请先配置好邮箱功能', cache=True)
        return
    sys.path.append(constants.LIB_PATH)
    from utils import emailUser
    dest_file = os.path.join(constants.TEMP_PATH, 'wxqr.png')
    wxbot.get_uuid()
    wxbot.gen_qr_code(dest_file)
    if os.path.exists(dest_file):
        mic.say(u'正在发送微信登录二维码到您的邮箱', cache=True)
        if emailUser(profile, u"这是您的微信登录二维码", "", [dest_file]):
            mic.say(u'发送成功', cache=True)
        else:
            mic.say(u'发送失败', cache=True)
    else:
        mic.say(u"微信接入失败", cache=True)


def isValid(text):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return all(word in text for word in ["微信", "二维码"])
