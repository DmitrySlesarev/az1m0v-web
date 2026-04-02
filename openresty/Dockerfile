FROM openresty/openresty:alpine

RUN apk add --no-cache bash

COPY entrypoint.sh /entrypoint.sh
COPY nginx-http.conf.template /etc/nginx/templates/nginx-http.conf.template
COPY nginx-https.conf.template /etc/nginx/templates/nginx-https.conf.template

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
