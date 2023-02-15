#!/bin/bash
cd frontend
echo "before go through"
python run.py & 
echo "go through"
cd ..
cd memcache
python run.py
