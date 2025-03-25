#!/bin/bash

set -e

for DATABASE in `psql -At -U postgres -c "select datname from pg_database where not datistemplate order by datname;" postgres`
do
  echo "Plain backup of $DATABASE"
  pg_dump -U postgres -Fc "$DATABASE" > /opt/backups/"$DATABASE".$(date -d "today" +"%Y-%m-%d-%H-%M").dump
done

find /opt/backups -mtime +7 -type f -delete
