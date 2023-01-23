# webapp Assignment 1 for 1779

##tutorial

add password.py with the content
    ```console
    password = "yourpassword"
    ```
Here replace "yourpassword" with your own password of MySQL.

Start the mem-cache.
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
    Usually, port number is 5000

Before connecting to database, add a password.py file in "/memcache/app" containing a variable password that is a string of your database password.
