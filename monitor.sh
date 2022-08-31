#!/bin/bash

device="${1}"
actions="device summary events details"
for action in ${actions}
do
  mkdir -p "${device}/${action}" > /dev/null 2>&1
done

while true
do 
  unique="$(date +%Y%m%d_%H%M%S)"
  success=0
  sleep_time=300
  printf "$(date "+%D %T") Gathering ${device} stats..."
  for action in ${actions}
  do
    printf "${action}..."
    fpath="${device}/${action}/${unique}"

    python cable_modem.py "${device}" "${action}" > "${fpath}.json" 2> "${fpath}.err"
    success=$?
    if [ ${success} -eq 0 ]
    then
      sleep_time=300
      rm -f "${fpath}.err"
    else
      sleep_time=30
      printf "FAILED..."
      break
    fi
  done

  printf "sleeping until $(date -v +${sleep_time}S "+%T")...\n"
  sleep ${sleep_time}
done

