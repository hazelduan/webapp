# web-app mem-cache


# Pre-requisite

Please ensure postgres database is running at localhost:5432 with username=admin and password with 12345


## Tutorial

### Development

#### Run without Docker

1. (Optional) Install virtual environment.

    ```console
    python3 -m venv .venv
    ```

2. (Optional) Activate virtual environment.

    ```console
    source .venv/bin/activate
    ```

3. Install dependencies.

    ```console

    pip3 install -r requirements.txt
    ```

4. Start Flask app

    ```console
    DB_HOST=localhost:5432 flask --debug run --port 8080
    ```
