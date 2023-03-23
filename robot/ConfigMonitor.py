# -*- coding: utf-8 -*-

import os
from robot import config, utils, logging
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class ConfigMonitor(FileSystemEventHandler):
    def __init__(self, conversation):
        FileSystemEventHandler.__init__(self)
        self._conversation = conversation

    # 文件修改
    def on_modified(self, event):
        if event.is_directory:
            return

        filename = event.src_path
        extension = os.path.splitext(filename)[-1].lower()
        if extension in (".yaml", ".yml"):
            if utils.validyaml(filename):
                logger.info(f"检测到文件 {filename} 发生变更")
                config.reload()
                self._conversation.reInit()
