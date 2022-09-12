#!/bin/bash

script_source="$(dirname ${0})"

cd "${script_source}"
source "${script_source}"/venv/bin/activate

etl_types="summary events details"

for etl_type in ${etl_types}
do
  etl_script="etl/${etl_type}.py"
  echo "$(date "+%D %T") Running ${etl_script}..."
  python "${etl_script}" motorola
done
echo "$(date "+%D %T") Complete"
