#!/bin/bash

#id="motorola"
#scheme="https"
#host="192.168.100.1"
#username="admin"
#password="abcde12345"
id="arris"
scheme="https"
host="192.168.100.1"
username="admin"
password="Abcde12345!"

actions="device summary events details"
for action in ${actions}
do
  mkdir -p "${action}" > /dev/null 2>&1
done

while true
do 
  unique="$(date +%Y%m%d_%H%M%S)"
  success=0
  sleep_time=300
  printf "$(date "+%D %T") Gathering stats..."
  for action in ${actions}
  do
    printf "${action}..."
    python motorola.py --scheme https --username admin --password abcde12345 "${action}" > "${action}/${unique}.json" 2> "${action}/${unique}.err"
    success=$?
    if [ ${success} -eq 0 ]
    then
      sleep_time=300
      rm -f "${action}/${unique}.err"
    else
      sleep_time=30
      printf "FAILED..."
      break
    fi
  done

  printf "sleeping until $(date -v +${sleep_time}S "+%T")...\n"
  sleep ${sleep_time}
done

