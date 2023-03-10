try:
    from database import password
except ImportError:
    raise ImportError('Create a password.py file store the password of the database')

db_user = 'root'
db_password = password.password
db_host = 'localhost'
db_name = 'webapp_db'

