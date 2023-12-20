#!/bin/sh

path="$1"
room=$2
session=$3
time=$4

echo $path

filename="${room}_${session}_${time}.tsc"

echo $filename
cat fullscene.tsc | sed -e "s#DATAPATH#$path#" | sed -e "s/ROOMPLACEHOLDER/$room/" | sed -e "s/SESSIONPLACEHOLDER/$session/" | sed -e "s/TIMEPLACEHOLDER/$time/" > $filename


sudo killall -9 jackd  
jackd -d coreaudio -r 48000 -p 64 &
sleep 2


tascar $filename 

# rm $filename
