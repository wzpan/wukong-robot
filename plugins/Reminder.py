# -*- coding: utf-8 -*-
# author: wzpan
# 闹钟

import logging
import os
import pickle
import time

from robot import config, constants, utils
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)

LOCAL_REMINDER = os.path.join(constants.TEMP_PATH, "reminder.pkl")


class Plugin(AbstractPlugin):
    def __init__(self, con):
        super(Plugin, self).__init__(con)

    def _dump_reminders(self):
        logger.info("写入日程提醒信息")
        with open(LOCAL_REMINDER, "wb") as f:
            pickle.dump(self.con.scheduler.get_jobs(), f)

    def alarm(self, remind_time, content, job_id):
        self.con.player.stop()  # 停止所有音频
        content = utils.stripPunctuation(content)
        self.say(
            f"现在是{time.strftime('%H:%M:%S', time.localtime(time.time()))}，该{content}了。"
            * int(config.get("/reminder/repeat", 3))
        )
        # 非周期性提醒，提醒完即删除
        if "repeat" not in remind_time:
            self.con.scheduler.del_job_by_id(job_id)
            self._dump_reminders()

    def list_reminder(self, parsed):
        """
        列举所有的日程
        """
        logger.info("list_reminder")
        _jobs = self.con.scheduler.get_jobs()
        if len(_jobs) == 0:
            self.say(f"您当前没有提醒。", cache=True)
        elif len(_jobs) > 1:
            self.say(f"您当前有{len(_jobs)}个提醒。", cache=True)
            index = 0
            for job in _jobs:
                self.say(f"第{index+1}个提醒内容是{job.describe}")
                logger.info(f"index: {index}, job.job_id: {job.job_id}")
                index += 1
        elif len(_jobs) == 1:
            self.say(f"您当前有1个提醒。", cache=True)
            self.say(f"提醒内容是{_jobs[0].describe}")

    def add_reminder(self, parsed):
        logger.info("add_reminder")
        remind_times = self.nlu.getSlotWords(parsed, "SET_REMIND", "user_remind_time")
        original_times = self.nlu.getSlotOriginalWords(
            parsed, "SET_REMIND", "user_remind_time"
        )
        contents = self.nlu.getSlotWords(parsed, "SET_REMIND", "user_wild_content")
        if len(remind_times) < 0 or "|" not in remind_times[0]:
            self.say("添加提醒失败。请说明需要我提醒的时间", cache=True)
            return
        if len(contents) < 0:
            self.say("添加提醒失败。请说明需要我提醒做什么", cache=True)
            return
        remind_time, original_time, content = (
            remind_times[0],
            original_times[0],
            contents[0],
        )
        job_id = utils.getTimemStap()
        job = self.con.scheduler.add_job(
            remind_time,
            original_time,
            content,
            lambda: self.alarm(remind_time, content, job_id),
            job_id=job_id,
        )
        if job:
            self._dump_reminders()
            logger.info(f"added reminder: {job.describe}, job_id: {job_id}")
            self.say(f"好的，已为您添加提醒：{job.describe}")
        else:
            self.say("抱歉，添加提醒失败了")

    def _assure(self):
        pick = self.activeListen()
        if "不" in pick:
            self.say("好的。取消删除", cache=True)
            return False
        elif any(yes in pick for yes in ("是", "要", "删除")):
            return True
        else:
            self.say("取消删除", cache=True)
            return False

    def _ask_which(self):
        self.say(f"要删除哪一个提醒呢", cache=True)
        pick = self.activeListen()
        parsed = self.parse(pick)
        if self.nlu.hasIntent(parsed, "HASS_INDEX"):
            _jobs = self.con.scheduler.get_jobs()
            index = int(
                float(
                    self.nlu.getSlotWords(parsed, "HASS_INDEX", "user_index")[0].split(
                        "|"
                    )[0]
                )
            )
            logger.info(f"用户选择了第{index}个")
            if index < 0 or index > len(_jobs):
                self.say("没有找到符合条件的提醒，删除失败", cache=True)
                return -1
            job = _jobs[index - 1]
            return job.job_id
        else:
            self.say("没有找到符合条件的提醒，删除失败", cache=True)
            return ""

    def del_reminder(self, parsed):
        logger.info("del_reminder")
        self.list_reminder(parsed)
        _jobs = self.con.scheduler.get_jobs()
        if len(_jobs) == 1:
            self.say("要删除这个提醒吗", cache=True)
            if self._assure():
                try:
                    self.con.scheduler.del_job_by_id(_jobs[0].job_id)
                    self._dump_reminders()
                    self.say("好的，已删除该提醒")
                except Exception as e:
                    logger.error(f"删除失败: {e}")
                    self.say("删除提醒失败")
        elif len(_jobs) > 1:
            job_id = self._ask_which()
            if job_id:
                try:
                    self.con.scheduler.del_job_by_id(job_id)
                    self._dump_reminders()
                    self.say("好的，已删除该提醒")
                except Exception as e:
                    logger.error(f"删除失败: {e}")
                    self.say("删除提醒失败")

    def handle(self, text, parsed):
        logger.info("Reminder handle")
        if self.nlu.hasIntent(parsed, "CHECK_REMIND"):
            # 查询当前设置的提醒
            self.list_reminder(parsed)
        elif self.nlu.hasIntent(parsed, "DELETE_REMIND"):
            # 删除指定的提醒
            self.del_reminder(parsed)
        elif self.nlu.hasIntent(parsed, "SET_REMIND"):
            # 设置提醒
            self.add_reminder(parsed)

    def isValid(self, text, parsed):
        return any(
            self.nlu.hasIntent(parsed, intent)
            for intent in ["CHECK_REMIND", "DELETE_REMIND", "SET_REMIND"]
        )
