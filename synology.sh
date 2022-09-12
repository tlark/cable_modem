#!/bin/bash

script_source="$(dirname ${0})"

cd "${script_source}"
source "${script_source}"/venv/bin/activate
python monitor.py motorola > monitor.out 2>&1
