#!/bin/bash

for i in {5001..5008}
do
    flask run --port $i &
done