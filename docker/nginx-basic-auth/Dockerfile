FROM nginx:1.27-alpine
RUN apk add --no-cache apache2-utils gettext
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
