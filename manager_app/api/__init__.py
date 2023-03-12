from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import boto3
import sys
sys.path.append('..')
sys.path.append('..')
from database import database_credential
from pathlib import Path

# from hashlib import md5
# from bintrees.rbtree import RBTree

from tools import cloudwatchAPI
<<<<<<< HEAD
=======
from flask_apscheduler import APScheduler
>>>>>>> 9dee058 (modify statistics page: 1. change statistics count from memcache to frontend(also change scheduler). 2. change cloud watch, along with average rate. 3. manager app fetch statistics from cloudwatch and store them to database, with scheduler. 4. fetch data from database and show it on the page)

manageapp = Flask(__name__)

manageapp.config['SECRET_KEY'] = 'dev' 

<<<<<<< HEAD
=======
class Config(object):
    SCHEDULER_API_ENABLED = True


manageapp.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(manageapp)
scheduler.start()

>>>>>>> 9dee058 (modify statistics page: 1. change statistics count from memcache to frontend(also change scheduler). 2. change cloud watch, along with average rate. 3. manager app fetch statistics from cloudwatch and store them to database, with scheduler. 4. fetch data from database and show it on the page)
db_user = database_credential.db_user
db_password = database_credential.db_password
db_host = database_credential.db_host
db_name = database_credential.db_name

# Add Database
manageapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(db_user, db_password, db_host, db_name)

# Initialize the Database
db = SQLAlchemy(manageapp)

with manageapp.app_context():
    db.create_all() # create_all() will only create tables that don't exist yet

BUCKET_NAME = 'webapp-image-storage'

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')

bucket_resp = s3.list_buckets()
for bucket in bucket_resp['Buckets']:
    print(bucket)

response = s3.list_objects_v2(Bucket=BUCKET_NAME)
if response['KeyCount'] != 0:
    for obj in response["Contents"]:
        print(obj)


cw_api = cloudwatchAPI.cloudwatchAPI()

from api import main


