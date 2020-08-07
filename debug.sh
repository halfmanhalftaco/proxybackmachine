#!/bin/bash

# build, run, execute a shell and destroy the container for debugging purposes.
# the local ./app dir is mounted so changes can be made live.
# this opens up the supervisord, uwsgi stats and redis ports too.

name=proxybackmachine
image=halfmanhalftaco/$name:latest

docker build --tag $image .
mkdir -p data/redis && chmod 777 data/redis
docker run -d --name $name -v $PWD/data:/data -v $PWD/app:/app -p 1080:1080 -p 1081:1081 -p 9001:9001 -p 6379:6379 $image 
docker exec -it $name /bin/sh
docker kill $name && docker rm $name
docker rmi $image
