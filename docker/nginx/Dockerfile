FROM nginx:1.27-bookworm

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl

RUN rm /etc/nginx/conf.d/default.conf

COPY docker/nginx/nginx.conf ./nginx.conf
COPY docker/nginx/default.conf ./default.conf

COPY docker/nginx/entrypoint.sh ./entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "-c", "./entrypoint.sh"]
