#!/bin/bash
cd frontend
echo "before go through"
python run.py & 
echo "manage app"
cd ..
cd manager_app
python run.py &
cd ..
cd memcache
for i in {5001..5008}
do
    flask run --port $i &
done
