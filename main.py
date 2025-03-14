import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Dict

import requests
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger("WeLinkPunchIn")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 按天滚动文件 Handler
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, "WeLinkPunchIn.log"),  # 基础文件名
    when="midnight",  # 每天午夜滚动
    interval=1,  # 每天生成一个文件
    backupCount=7,  # 保留最近7天日志
    encoding="utf-8",
    delay=False,
    utc=False  # 使用本地时间
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def load_config(config_path: str = "conf.yaml") -> Dict[str, str]:
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            conf = yaml.safe_load(f)
            logger.info("配置文件加载成功")
            return conf["app"]
        except yaml.YAMLError as exc:
            logger.error(f'加载配置文件失败: {exc}')
            raise


def trigger_hamibot_task(job_type):
    """触发Hamibot任务（上班或下班）"""
    try:
        conf = load_config()
        url = f"https://api.hamibot.com/v1/devscripts/{conf['SCRIPT_ID']}/run"
        headers = {
            "Authorization": f"{conf['API_KEY']}",
            "Content-Type": "application/json"
        }
        payload = {"devices": [{'_id': conf['DEVICE_ID']}]}
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 204:
            logger.info(f"{job_type}打卡任务触发成功")
        else:
            logger.error(f"{job_type}打卡失败: {resp.text}")
    except Exception as e:
        logger.error(f"请求异常: {str(e)}")


def configure_schedules(scheduler):
    """配置所有定时规则"""

    # ---------------------------
    # 上班触发器（每天 08:25~09:30，每5分钟）
    # ---------------------------
    scheduler.add_job(
        trigger_hamibot_task,
        CronTrigger(
            day_of_week="mon-fri",  # 仅工作日
            hour="8-9",  # 8点到9点
            minute="25-59/5" if 8 else "0-30/5"  # 8点:25-59分每5分钟；9点:00-30分每5分钟
        ),
        args=["上班"],
        id="work_check"
    )

    # ---------------------------
    # 下班触发器（动态周规则）
    # ---------------------------
    # 规则1：周一/二/四 20:30~21:30，每5分钟
    scheduler.add_job(
        trigger_hamibot_task,
        CronTrigger(
            day_of_week="mon,tue,thu",
            hour="20-21",
            minute="30-59/5" if 20 else "0-30/5"  # 20点:30-59分；21点:00-30分
        ),
        args=["下班-普通日"],
        id="off_check_normal"
    )

    # 规则2：周三/五 18:30~19:30，每5分钟
    scheduler.add_job(
        trigger_hamibot_task,
        CronTrigger(
            day_of_week="wed,fri",
            hour="18-19",
            minute="30-59/5" if 18 else "0-30/5"  # 18点:30-59分；19点:00-30分
        ),
        args=["下班-特殊日"],
        id="off_check_special"
    )


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    configure_schedules(scheduler)
    logger.info("定时任务已启动，按 Ctrl+C 退出")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()
    # trigger_hamibot_task("")
