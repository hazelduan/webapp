from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import boto3
import sys
sys.path.append('..')
sys.path.append('..')
from database import database_credential
from pathlib import Path
from hashlib import md5
from bintrees.rbtree import RBTree


manageapp = Flask(__name__)


manageapp.config['SECRET_KEY'] = 'dev' 



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


# consistent hashing
# def _not_exists(key):
#     return key is None or key == -1

# def find_upper(root, elem):
#     if root is None:
#         return -1

#     if elem == root.key:
#         return root.key
#     elif elem < root.key:
#         maybe_max = find_upper(root.left, elem)
#         if _not_exists(maybe_max):
#             return root.key
#         return maybe_max
#     else:
#         maybe_max = find_upper(root.right, elem)
#         if _not_exists(maybe_max):
#             return -1
#         return maybe_max

# def find_lower(root, elem):
#     if root is None:
#         return -1
#     if elem == root.key:
#         return root.key
#     elif elem < root.key:
#         maybe_min = find_lower(root.left, elem)
#         if _not_exists(maybe_min):
#             return -1
#         return maybe_min
#     else:
#         maybe_min = find_lower(root.right, elem)
#         if _not_exists(maybe_min):
#             return root.key
#         return maybe_min

# def find_next(root, elem):
#     if root is None:
#         return None, None
#     return find_lower(root, elem), find_upper(root, elem)

# def trace_tree(root):
#     if root:
#         print("{} {} {}".format(
#             root.key,
#             root.left.key if root.left is not None else None,
#             root.right.key if root.right is not None else None))
#         trace_tree(root.left)
#         trace_tree(root.right)

# class CHNode(object):
#     def __init__(self, host_name, id=None, vhost=None):
#         self._id = id
#         self.host_name = host_name
#         if vhost:
#             self._hash_host_name = "{}#{}".format(host_name, vhost)
#         else:
#             self._hash_host_name = host_name

#     def get_id(self, ch_size):
#         if self._id:
#             return self._id
#         return int(md5(self._hash_host_name.encode("utf-8")).hexdigest(), 16) % ch_size

# class ConsistHash(object):
#     def __init__(self, size=0xffff):
#         self.size = size # set consistent hash circul size
#         self.rbt = RBTree()  # red black tree

#     def insert_host(self, host):
#         host_id = host.get_id(self.size)
#         self.rbt.insert(host_id, host)

#     def remove_host(self, host):
#         host_id = host.get_id(self.size)
#         self.rbt.remove(host_id)

#     @staticmethod
#     def _find_upper(root, elem):
#         if root is None:
#             return -1

#         if elem == root.key:
#             return root.key
#         elif elem < root.key:
#             maybe_max = find_upper(root.left, elem)
#             if _not_exists(maybe_max):
#                 return root.key
#             return maybe_max
#         else:
#             maybe_max = find_upper(root.right, elem)
#             if _not_exists(maybe_max):
#                 return -1
#             return maybe_max

#     def find_host(self, id):
#         id %= self.size
#         idx = self._find_upper(self.rbt._root, id)
#         if idx == -1:  # id larger than max id
#             # assert tree is not empty
#             return self.rbt.min_item()[1]
#         return self.rbt.get_value(idx)


from api import main  

