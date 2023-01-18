# web-app mem-cache


## Prerequisite


## Tutorial

### Development

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
    DB_HOST=localhost:5432 flask --debug run --port 8080
    ```
