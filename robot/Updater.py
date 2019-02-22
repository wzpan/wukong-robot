import os
import requests
import json
import semver
from subprocess import call
from robot import constants, logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

_updater = None
URL = 'https://service-e32kknxi-1253537070.ap-hongkong.apigateway.myqcloud.com/release/wukong'

class Updater(object):

    def __init__(self):
        self.last_check = datetime.now() - timedelta(days=1.5)
        self.update_info = {}

    def _pull(self, cwd, tag):
        if os.path.exists(cwd):
            return call(['git checkout master && git pull && git checkout {}'.format(tag, tag, tag)], cwd=cwd, shell=True) == 0
        else:
            logger.error("目录 {} 不存在".format(cwd))
            return False

    def _pip(self, cwd):
        if os.path.exists(cwd):
            return call(['pip3', 'install', '-r', 'requirements.txt'], cwd=cwd, shell=False) == 0
        else:
            logger.error("目录 {} 不存在".format(cwd))
            return False

    def update(self):
        update_info = self.fetch()
        success = True
        if update_info == {}:
            logger.info('恭喜你，wukong-robot 已经是最新！')
        if 'main' in update_info:
            if self._pull(constants.APP_PATH, update_info['main']['version']) and self._pip(constants.APP_PATH):
                logger.info('wukong-robot 更新成功！')
                self.update_info.pop('main')
            else:
                logger.info('wukong-robot 更新失败！')
                success = False
        if 'contrib' in update_info:
            if self._pull(constants.CONTRIB_PATH, update_info['contrib']['version']) and self._pip(constants.CONTRIB_PATH):
                logger.info('wukong-contrib 更新成功！')
                self.update_info.pop('contrib')
            else:
                logger.info('wukong-contrib 更新失败！')
                success = False
        return success

    def _get_version(self, path, current):
        if os.path.exists(os.path.join(path, 'VERSION')):
            with open(os.path.join(path, 'VERSION'), 'r') as f:
                return f.read().strip()
        else:
            return current

    def fetch(self):
        global URL
        now = datetime.now()
        if (now - self.last_check).seconds <= 1800:
            logger.debug('30 分钟内已检查过更新，使用上次的检查结果：{}'.format(self.update_info))            
            return self.update_info
        try:
            self.last_check = now
            r = requests.get(URL, timeout=3)
            info = json.loads(r.text)
            main_version = info['main']['version']
            contrib_version = info['contrib']['version']
            # 检查主仓库
            current_main_version = self._get_version(constants.APP_PATH, main_version)
            current_contrib_version = self._get_version(constants.CONTRIB_PATH, contrib_version)
            if semver.compare(main_version, current_main_version) > 0:
                logger.info('主仓库检查到更新：{}'.format(info['main']))
                self.update_info['main'] = info['main']
            if semver.compare(contrib_version, current_contrib_version) > 0:
                logger.info('插件库检查到更新：{}'.format(info['contrib']))
                self.update_info['contrib'] = info['contrib']
            if 'notices' in info:
                self.update_info['notices'] = info['notices']
            return self.update_info
        except Exception as e:
            logger.error("检查更新失败：", e)
            res = {}

def fetch():
    global _updater
    if not _updater:
        _updater = Updater()
    return _updater.fetch()
    
    
if __name__ == '__main__':
    fetch()
