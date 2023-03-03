from flask import Flask
from flask_apscheduler import APScheduler

import sys
sys.path.append('..')
sys.path.append('..')
from tools import cloudwatchAPI

autoscaler = Flask(__name__)

# Scheduler

class Config(object):
    SCHEDULER_API_ENABLED = True


autoscaler.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(autoscaler)

# CloudWatch
cw_api = cloudwatchAPI.cloudwatchAPI()
from app import main