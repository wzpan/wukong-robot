import requests
import json
import logging
from uuid import getnode as get_mac

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TulingRobot():

    SLUG = "tuling"

    def __init__(self, tuling_key):
        """
        图灵机器人
        """
        super(self.__class__, self).__init__()
        self.tuling_key = tuling_key

    def chat(self, texts):
        """
        使用图灵机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = ''.join(texts)
        try:
            url = "http://www.tuling123.com/openapi/api"
            userid = str(get_mac())[:32]
            body = {'key': self.tuling_key, 'info': msg, 'userid': userid}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            elif respond['code'] == 200000:
                result = respond['url']
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                        k['article'] + "\t" + k['detailurl'] + "\n"
            else:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            logger.info('图灵回答：' + result)
            return result
        except Exception:
            logger.critical("Tuling robot failed to responsed for %r",
                                  msg, exc_info=True)            
