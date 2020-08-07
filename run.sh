#!/bin/bash

image=halfmanhalftaco/proxybackmachine:latest
mkdir -p data/redis && chmod 777 data/redis
docker run --name proxybackmachine -d -v $PWD/data:/data -p 1080:1080 $image
