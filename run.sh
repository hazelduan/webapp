#!/bin/bash
cd frontend
echo "before go through"
python run.py & 
echo "go through to memcache"
cd ..
cd memcache
python run.py &
echo "manage app"
cd ..
cd manage_app
python run.py
