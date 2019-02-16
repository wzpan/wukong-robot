# -*- coding: utf-8-*-

import os
import shutil
from robot import constants
from robot.sdk.AbstractPlugin import AbstractPlugin

class Plugin(AbstractPlugin):

    SLUG = 'cleancache'

    def handle(self, text, parsed):
        temp = constants.TEMP_PATH
        for f in os.listdir(temp):
            if os.path.isfile(os.path.join(temp, f)):
                os.remove(os.path.join(temp, f))
            else:
                shutil.rmtree(os.path.join(temp, f))
        self.say(u'缓存目录已清空', cache=True)

    def isValid(self, text, parsed):
        return any(word in text.lower() for word in ["清除缓存", u"清空缓存", u"清缓存"])
