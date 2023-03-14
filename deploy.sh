#!/bin/bash

cd database
echo "password='trWoatpKnyutPqx8an6u'" > password.py
cd ..
. ../venv/bin/activate
cd memcache/
flask run
