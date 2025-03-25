#!/bin/bash

set -e

GREEN="\e[92m"
RED='\e[31m'

/wait-for-postgres.sh

. /opt/pysetup/.venv/bin/activate

printf $RED"*******************************\n"
printf $RED"*******************************\n"
printf $GREEN"Starting Production Environment\n"
printf $RED"*******************************\n"
printf $RED"*******************************\n"

if [ "$1" = "runserver" ]; then
    printf $GREEN"Running... -> Gunicorn Server\n"
    chmod +x run
    exec ./run
elif [ "$1" = 'test' ]; then
	  pytest -v --cov=. --cov-fail-under=$COV_FAIL_THRESHOLD
else
	  exec "$@"
fi

exit
