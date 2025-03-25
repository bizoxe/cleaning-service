#!/bin/bash

GREEN="\e[92m"
RED="\e[31m"

printf $RED"*******************************\n"
printf $GREEN"Preparing for NGINX launch\n"
printf $RED"*******************************\n"

export ALLOWED_TO_REPLACE=$(printenv | grep '^API_' | cut -d '=' -f 1 | awk '{print "${"$1"}"}' | tr '\n' ' ')

envsubst "$ALLOWED_TO_REPLACE" < ./default.conf > /tmp/default.conf
envsubst "$ALLOWED_TO_REPLACE" < ./nginx.conf > /tmp/nginx.conf

if [ -n "$API_CONFIG_DEBUG" ]; then
  echo "Debugging is enabled, printing configuration files:"
  echo -e "/tmp/nginx.conf\n\n"
  cat /tmp/nginx.conf
  echo -e "/tmp/default.conf\n\n"
  cat /tmp/default.conf
fi

echo -e "${GREEN}Starting NGINX...\n"

nginx -c /tmp/nginx.conf -g "daemon off;"
