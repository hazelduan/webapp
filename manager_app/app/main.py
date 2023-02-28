from flask import render_template, url_for, request
from app import managerapp
from flask import json

import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

@managerapp.route('/')
def main():
    html = '''
        <!DOCTYPE html>
            <html>
                <head>
                    <title>manager index</title>
                </head>
                <body>
                    <h2>manager index</h2>
                </body>
            </html>
        '''
    return html




