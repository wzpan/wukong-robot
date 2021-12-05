# -*- coding: utf -8-*-

from . import config
import uuid
import requests
import threading


def getUUID():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e : e + 2] for e in range(0, 11, 2)])


def report(t):
    ReportThread(t).start()


class ReportThread(threading.Thread):
    def __init__(self, t):
        # 需要执行父类的初始化方法
        threading.Thread.__init__(self)
        self.t = t

    def run(self):
        to_report = config.get("statistic", True)
        if to_report:
            try:
                persona = config.get("robot_name_cn", "孙悟空")
                url = "http://livecv.hahack.com:8022/statistic"
                payload = {
                    "type": str(self.t),
                    "uuid": getUUID(),
                    "name": persona,
                    "project": "wukong",
                }
                requests.post(url, data=payload, timeout=3)
            except Exception:
                return
