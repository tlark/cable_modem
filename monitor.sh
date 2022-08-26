#!/bin/bash

actions="summary events details"
for action in ${actions}
do
    mkdir -p "${action}" > /dev/null 2>&1
done

while true
do 
    unique="$(date +%Y%m%d_%H%M%S)"
    printf "Gathering stats for ${unique}..."
    for action in ${actions}
    do
        python motorola.py --scheme https --username admin --password abcde12345 "${action}" | jsonpp > "${action}/${unique}.log"
    done
    printf "sleeping for 300 seconds...\n"
    sleep 300 
done

