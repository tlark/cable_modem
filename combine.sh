#!/bin/bash

script_source="$(dirname ${0})"

cd "${script_source}"
source "${script_source}"/venv/bin/activate

etl_types="summary events details"

device_id="${1}"

for etl_type in ${etl_types}
do
  etl_script="etl/${etl_type}.py"
  echo "$(date "+%D %T") Running ${etl_script} ${device_id}..."
  python "${etl_script}" "${device_id}"
done
echo "$(date "+%D %T") Complete"
