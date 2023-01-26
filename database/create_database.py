import mysql.connector
import database_credential
mydb = mysql.connector.connect(
    host=database_credential.db_host,
    user=database_credential.db_user,
    passwd=database_credential.db_password,
    )

my_cursor = mydb.cursor();
my_cursor.execute(("CREATE DATABASE {}".format(database_credential.db_name)))

my_cursor.execute("SHOW DATABASES")
for db in my_cursor:
    print(db)