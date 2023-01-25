from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import webapp
from flask import render_template, url_for, request
from app import database_credential
import os
db_user = database_credential.db_user
db_password = database_credential.db_password
db_host = database_credential.db_host
db_name = database_credential.db_name

# Add Database
webapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(db_user, db_password, db_host, db_name)
# webapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql:///' + os.path.dirname(__file__) + '/data.db'
# Secret Key
# webapp.config['SECRET_KEY'] = "a"

# Initialize the Database
db = SQLAlchemy(webapp)

class Images(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    image_key = db.Column(db.String(50))
    image = db.Column(db.String(50))
