#!/bin/bash

script_source="$(dirname ${0})"

cd "${script_source}"
source "${script_source}"/venv/bin/activate

device_id="${1}"
python monitor.py "${device_id}"
