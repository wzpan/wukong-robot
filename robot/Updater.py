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

    def _pull(self, cwd):
        if os.path.exists(cwd):
            return call(['git', 'pull'], cwd=cwd, shell=False) == 0
        else:
            logger.error("目录 {} 不存在".format(cwd))
            return False

    def _pip(self, cwd):
        if os.path.exists(cwd):
            return call(['pip', 'install', '-r', 'requirements.txt'], cwd=cwd, shell=False) == 0
        else:
            logger.error("目录 {} 不存在".format(cwd))
            return False

    def update(self):
        if self._pull(constants.APP_PATH) and self._pip(constants.APP_PATH):
            logger.info('wukong-robot 更新成功！')
        else:
            logger.info('wukong-robot 更新失败！')
        if self._pull(constants.CONTRIB_PATH) and self._pip(constants.CONTRIB_PATH):
            logger.info('wukong-contrib 更新成功！')
        else:
            logger.info('wukong-contrib 更新失败！')

    def _get_version(self, path, current):
        if os.path.exists(os.path.join(path, 'VERSION')):
            with open(os.path.join(path, 'VERSION'), 'r') as f:
                return f.read().strip()
        else:
            return current

    def fetch(self):
        global URL
        now = datetime.now()
        if (now - self.last_check).days <= 0:
            logger.debug('当天已检查过更新，使用上次的检查结果：{}'.format(self.update_info))            
            return self.update_info
        try:
            self.last_check = now
            r = requests.get(URL)
            info = json.loads(r.text)
            main_version = info['main']['version']
            contrib_version = info['contrib']['version']
            # 检查主仓库
            current_main_version = self._get_version(constants.APP_PATH, main_version)
            current_contrib_version = self._get_version(constants.CONTRIB_PATH, contrib_version)
            if semver.compare(main_version, current_main_version):
                logger.info('主仓库检查到更新：{}'.format(info['main']))
                self.update_info['main'] = info['main']
            if semver.compare(contrib_version, current_contrib_version):
                logger.info('插件库检查到更新：{}'.format(info['contrib']))
                self.update_info['contrib'] = info['contrib']
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
