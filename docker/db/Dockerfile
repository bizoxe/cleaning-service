FROM postgres:16.8-bookworm

RUN mkdir -p /opt/backups
COPY docker/db/pgbackup.sh /opt/pgbackup.sh
RUN chmod +x /opt/pgbackup.sh

RUN mkdir -p /docker-entrypoint-initdb.d
COPY docker/db/init-database.sh /docker-entrypoint-initdb.d

VOLUME ["/opt/backups"]
