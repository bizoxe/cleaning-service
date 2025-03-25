#!/bin/bash

set -e

GREEN="\e[92m"
RED='\e[31m'
PYTEST_CACHE_DIR=.pytest_cache

/wait-for-postgres.sh

. /opt/pysetup/.venv/bin/activate

printf $RED"*******************************\n"
printf $GREEN"Starting Development Environment\n"
printf $RED"*******************************\n"

if [ "$1" = "runserver" ]; then
    printf $GREEN"Running... -> Uvicorn Server\n"
	  python main.py
elif [ "$1" = 'test' ]; then
    if [ -d "$PYTEST_CACHE_DIR" ]; then rm -Rf $PYTEST_CACHE_DIR; fi
    pytest -v --cov-config=.coveragerc --cov-fail-under=$COV_FAIL_THRESHOLD --cov=. .
else
	  exec "$@"
fi

exit
