import mysql.connector
import sys
import logging
sys.path.append("..")
sys.path.append("..")
from database import database_credential
from configuration import base_path, file_system_path, backend_base_url


from flask import render_template, url_for, request, flash, redirect
from api import manageapp
from flask import json
import requests
import os
from api import db
from pathlib import Path
import base64
import boto3

import datetime
x = datetime.datetime.now() #just for test


logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = 'webapp-image-storage'

s3 = boto3.client('s3')

bucket_resp = s3.list_buckets()
for bucket in bucket_resp['Buckets']:
    print(bucket)

response = s3.list_objects_v2(Bucket=BUCKET_NAME)
if response['KeyCount'] != 0:
    for obj in response["Contents"]:
        print(obj)

@manageapp.route('/api/time')
def get_time():
    return {
        'Name':"hazel", 
        "Date":x, 
        "programming":"python"
        }

