#!/bin/bash

RED='\e[31m'
GREEN="\e[92m"

export WAIT_HOSTS="$APP_CONFIG__DB__POSTGRES_HOST:$APP_CONFIG__DB__POSTGRES_PORT"
export WAIT_TIMEOUT=300
export WAIT_SLEEP_INTERVAL=30
export WAIT_HOST_CONNECT_TIMEOUT=30
printf $RED"*******************************\n"
printf $GREEN"Waiting for $WAIT_HOSTS\n"
printf $RED"*******************************\n"
/wait
