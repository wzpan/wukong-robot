import os

from robot import constants, logging

logger = logging.getLogger(__name__)

class Updater(object):

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
    
