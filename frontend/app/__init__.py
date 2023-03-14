from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import boto3
import mysql.connector
from flask_apscheduler import APScheduler
import sys
sys.path.append('..')
sys.path.append('..')
from database import database_credential
from tools import cloudwatchAPI


webapp = Flask(__name__)


webapp.config['SECRET_KEY'] = 'dev' 

# Scheduler

class Config(object):
    SCHEDULER_API_ENABLED = True


webapp.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(webapp)
#scheduler.start()

db_user = database_credential.db_user
db_password = database_credential.db_password
db_host = database_credential.db_host
db_name = database_credential.db_name

# Add Database
webapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(db_user, db_password, db_host, db_name)


# Initialize the Database
db = SQLAlchemy(webapp)


class Images(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    image_key = db.Column(db.String(50))
    image_path = db.Column(db.String(100))

with webapp.app_context():
    db.create_all() # create_all() will only create tables that don't exist yet

    # Amazon S3 Initialization
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


# clear the memcache statistics
# the reason why do this here is that there will be time gap among multiple nodes when start,
# and delete database needs time, may trigger synchronization problems
mydb = mysql.connector.connect(
        host=database_credential.db_host,
        user=database_credential.db_user,
        passwd=database_credential.db_password,
    )
my_cursor = mydb.cursor()
my_cursor.execute(("USE {};".format(database_credential.db_name)))
my_cursor.execute(("TRUNCATE memcache_statistics;"))

# creating ec2 instance
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
# ec2.create_instances(ImageId='ami-006dcf34c09e50022', MinCount=1, MaxCount=8,
# data accumulator
class DataAccumulator:
    def __init__(self):
        self.data = {
            'node_num': 0,
            'request_num': 0,
            'hit_num': 0,
            'miss_num': 0,
            'lookup_num': 0,
            'item_num': 0,
            'total_size': 0.0,
        }
    def add(self, key, value):
        if key in self.data:
            self.data[key] += value
        else:
            self.data[key] = value
    def get(self, key):
        return self.data[key]
    def clear(self):
        self.data = {
            'node_num': 0,
            'request_num': 0,
            'hit_num': 0,
            'miss_num': 0,
            'lookup_num': 0,
            'item_num': 0,
            'total_size': 0.0,
        }
    def get_all(self):
        return self.data

statistics = DataAccumulator()

# # creating ec2 instance
# ec2 = boto3.resource('ec2')
# ec2.create_instances(ImageId='ami-006dcf34c09e50022', MinCount=1, MaxCount=1,
#                      InstanceType='t2.micro', SubnetId='subnet-03cdead617e2d0d41')
cw_api = cloudwatchAPI.cloudwatchAPI()

ssm_client = boto3.client('ssm')

from app import main




