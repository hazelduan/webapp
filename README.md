# webapp Assignment 1 for 1779
THis is the instructions for assign1, including db config, and flask run.

## Database config
1. Before all running commands, it is necessary to update database in local system. First, use
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

## Start the mem-cache.
1. (Optional) Install virtual environment.

    ```console
    python3 -m venv .venv
    ```

2. (Optional) Activate virtual environment.

    ```console
    source .venv/bin/activate
    ```
    if wanna quit, use deactivate

3. Install dependencies.

    ```console

    pip3 install -r requirements.txt
    ```

4. Start Flask app

    ```console
    FLASK_APP=run.py
    ```
    ```console
    DB_HOST=localhost:hostnumber flask --debug run --port <portnumber>
    ```
    Frontend port number is 5000, backend is 5001. DB by default is 3306.

