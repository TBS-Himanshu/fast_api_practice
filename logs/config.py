import logging
from logging.handlers import TimedRotatingFileHandler
import os
import json


LOG_DIR='log_files'
os.makedirs(LOG_DIR, exist_ok=True)


logger = logging.getLogger('request_logger')
logger.setLevel(logging.INFO)

handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, 'requests.log'),
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)


def log_event(data: dict):
    logger.info(json.dumps(data, default=str))
logger.addHandler(handler)