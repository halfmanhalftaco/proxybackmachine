FROM alpine:latest
RUN apk add --no-cache python3 uwsgi uwsgi-python3 uwsgi-http supervisor redis py3-redis
EXPOSE 1080/tcp 1081/tcp 9001/tcp 6379/tcp
COPY ./app /app
CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"]
