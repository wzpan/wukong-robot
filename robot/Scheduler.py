# wukong-robot 的提醒机制
# 基于 BackgroundScheduler 做二次封装
import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from robot import logging, utils, constants

logger = logging.getLogger(__name__)


class Job(object):
    """
    任务类
    """

    def __init__(self, remind_time, original_time, content, describe, job_id):
        self.remind_time = remind_time
        self.original_time = original_time
        self.content = utils.stripPunctuation(content)
        self.describe = describe
        self.job_id = job_id


class Scheduler(object):
    """
    wukong-robot 的提醒器，
    用于实现日程提醒功能
    """

    def __init__(self, con):
        self._jobs = []
        self._sched = BackgroundScheduler()
        self._sched.start()
        self.con = con

    def _get_datetime(self, norm_str):
        date, time = norm_str.split("|")
        year, mon, day = date.split("-")
        hour, min, sec = time.split(":")
        return datetime.datetime(
            int(year), int(mon), int(day), int(hour), int(min), int(sec)
        )

    def _add_interval_job(self, alarm, job_id, norm_str):
        interval, count = norm_str.split("-")[1:]
        interval_type = interval + "s"
        self._sched.add_job(
            alarm,
            "interval",
            **{interval_type: int(count)},
            id=job_id,
            misfire_grace_time=60,
        )
        return True

    def _parse_cron_rule(self, rule_str):
        # 解析规则字符串
        rule_type, rule_time = rule_str.split("|")
        rule_time_parts = rule_time.split(" ")
        hour, minute, second = 0, 0, 0
        if len(rule_time_parts) > 1:
            hour, minute, second = map(int, rule_time_parts[1].split(":"))
        else:
            hour, minute, second = map(int, rule_time_parts[0].split(":"))

        if rule_type.startswith("repeat-day"):
            # 每天执行
            return CronTrigger(second=second, minute=minute, hour=hour)
        elif rule_type.startswith("repeat-week"):
            # 每周执行
            day_of_week = rule_time_parts[0].split("-")[1]
            return CronTrigger(
                second=second, minute=minute, hour=hour, day_of_week=day_of_week
            )
        elif rule_type.startswith("repeat-month"):
            # 每月执行
            day_of_month = rule_time_parts[0].split("-")[1]
            return CronTrigger(
                second=second, minute=minute, hour=hour, day=day_of_month
            )
        elif rule_type.startswith("repeat-year"):
            # 每年执行
            month, day = rule_time_parts[0].split("-")
            return CronTrigger(
                second=second, minute=minute, hour=hour, day=day, month=month
            )
        else:
            return None

    def _add_cron_job(self, alarm, job_id, norm_str):
        # 解析规则字符串
        cron_trigger = self._parse_cron_rule(norm_str)
        if cron_trigger:
            self._sched.add_job(alarm, trigger=cron_trigger, misfire_grace_time=60)
            return True
        return False

    def get_jobs(self):
        """
        检查当前有多少提醒

        """
        return self._jobs

    def set_jobs(self, jobs):
        self._jobs = jobs

    def add_job(self, remind_time, original_time, content, onAlarm, job_id=None):
        """
        添加提醒

        :param remind_time: 提醒时间
        :param content: 提醒事项
        :param onAlarm: 提醒的时候触发的响应
        :returns: 添加成功：添加的提醒；添加失败：None
        """
        if not job_id:
            job_id = utils.getTimemStap()

        job = Job(
            remind_time=remind_time,
            original_time=original_time,
            content=content,
            describe=f"时间：{remind_time}，事项：{content}"
            if "repeat" not in remind_time
            else f"时间：{original_time}, 事项：{content}",
            job_id=job_id,
        )
        success = False
        if "repeat" in remind_time:
            if "|" in remind_time:
                # cron 任务
                success = self._add_cron_job(onAlarm, job_id, remind_time)
            else:
                # interval 任务
                success = self._add_interval_job(onAlarm, job_id, remind_time)
        else:
            success = self._sched.add_job(
                onAlarm,
                "date",
                run_date=self._get_datetime(remind_time),
                id=job_id,
                misfire_grace_time=60,
            )
        if success:
            self._jobs.append(job)
            return job
        return None

    def has_job(self, job_id):
        return self._sched.get_job(job_id)

    def del_job_by_id(self, job_id):
        """
        删除指定 job_id 的提醒

        :param job_id: 提醒id
        """
        try:
            if self._sched.get_job(job_id=job_id):
                self._sched.remove_job(job_id=job_id)
            self._jobs = [job for job in self._jobs if job.job_id != job_id]
        except Exception as e:
            logger.warning(f"id {job_id} 的提醒已被删除。删除失败。")
