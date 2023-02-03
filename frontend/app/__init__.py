from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
sys.path.append('..')
sys.path.append('..')
from database import database_credential
from pathlib import Path

webapp = Flask(__name__)


webapp.config['SECRET_KEY'] = 'dev' 



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


import app.main




