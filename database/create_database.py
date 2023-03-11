import mysql.connector
#import database_credential
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    #passwd=database_credential.db_password,
    passwd="ece1779pass"
    )

my_cursor = mydb.cursor()
my_cursor.execute(("CREATE DATABASE webapp_db"))
my_cursor.execute(("USE webapp_db;"))
#my_cursor.execute(("SELECT * FROM MEMCACHE_STATISTICS"))
my_cursor.execute("SHOW DATABASES")
for db in my_cursor:
    print(db)
    print(db[0])
