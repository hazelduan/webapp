# webapp Assignment 2 for 1779
THis is the instructions for assign2, including db config, and flask run.

## Database config(now the database is in RDS so no need to rebuild the table everytime)
1. Before all running commands, update database in if necessary. First, use
    ```console
    flask shell
    ```
Attention : need to be in frontend or memcache folder for flask need to find an app to run this command.

2. Rebuild table

    ```console
    from app import db
    ```
    ```console
    db.drop_all()
    ```
    ```console
    db.create_all()
    ```
    
3. Before connecting to database, add a password.py file in "/database" containing a variable password that is a string of your database password.

    ```console
    password = "yourpassword"
    ```
Here replace "yourpassword" with your own password of MySQL.

## Start flask instance.
1. (Optional) Install virtual environment.

    ```console
    python3 -m venv venv
    ```

2. (Optional) Activate virtual environment.

    ```console
    source venv/bin/activate
    ```
    if wanna quit, use deactivate

3. Install dependencies.

    ```console

    pip3 install -r requirements.txt
    ```

4. Start Flask app

Now simply use one shell script.
    ```console
    sh run.sh
    ```
    if Ubuntu, use
    ```console
    ./run.sh
    ```
    The other way is to run each flask instance separately
    
    ```console
    FLASK_APP=run.py
    ```
    ```console
    DB_HOST=localhost:hostnumber flask --debug run --port <portnumber>
    ```
    Frontend port number is 5000, DB is 3306, autoscaler is 5020, memcache 5001-5008 and manager app is 8001.

