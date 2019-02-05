# -*- coding: utf-8-*-

from robot import config
from watchdog.events import *

class ConfigMonitor(FileSystemEventHandler):
    def __init__(self, conversation):
        FileSystemEventHandler.__init__(self)
        self._conversation = conversation

    # 文件修改
    def on_modified(self, event):
        if not event.is_directory:
            config.reload()
            self._conversation.reload()
