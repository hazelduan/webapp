#!/bin/bash

function trap_ctrlc ()
{
    # perform cleanup here
    echo "Ctrl-C caught...performing clean up"

    echo "Doing cleanup"
    kill -9 ${PID1}
    kill -9 ${PID2}

    kill -9 ${PID5001}
    kill -9 ${PID5002}
    kill -9 ${PID5003}
    kill -9 ${PID5004}
    kill -9 ${PID5005}
    kill -9 ${PID5006}
    kill -9 ${PID5007}
    kill -9 ${PID5008}
    # exit shell script with error code 2
    # if omitted, shell script will continue execution
    exit 2
}
trap "trap_ctrlc" 2


cd frontend
echo "before go through"
python run.py &
PID1=$!
echo ${PID1}
echo "manage app"
cd ..
cd manager_app
python run.py &
PID2=$!
echo ${PID2}
cd ..
cd auto_scaler
python run.py &
cd ..
cd memcache


flask run --port 5001 &
PID5001=$!
echo ${PID5001}
flask run --port 5002 &
PID5002=$!
echo ${PID5002}
flask run --port 5003 &
PID5003=$!
echo ${PID5003}
flask run --port 5004 &
PID5004=$!
echo ${PID5004}
flask run --port 5005 &
PID5005=$!
echo ${PID5005}
flask run --port 5006 &
PID5006=$!
echo ${PID5006}
flask run --port 5007 &
PID5007=$!
echo ${PID5007}
flask run --port 5008 &
PID5008=$!
echo ${PID5008}
wait