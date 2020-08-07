proxybackmachine
================

`proxybackmachine` is an HTTP proxy that uses the [Internet Archive's](https://www.archive.org) [Wayback Machine](https://web.archive.org/) as the source. This allows you to point old computers at the proxy and browse the web as if it was an arbitrary date in the past. Performance is not great but it gets the job done.

To use, start the docker container and then configure a browser to use the HTTP proxy at `<your_ip>:1080`. No other configuration is necessary.

### What works

* Any site that archive.org has enough data for (1996ish on) via HTTP

### What doesn't work

* Any https://, ftp://, gopher://, etc URLs.

The proxy defaults to June 1st, 1999 but can be set (from the machine) by browsing to:

http://proxy/?date=20151105 

or

http://www.proxyback.com/?date=20151105

where the date parameter is the date you want to set. Format is `YYYY[MM[DD][hhmm[ss]]]`. This is used to query the Wayback Machine to find the nearest capture avaliable per request. This setting is per-IP so you can have several machines on your network set to different points in time.

A status page (at http://proxy/ or http://www.proxyback.com/ ) shows some debug data and what the proxy is currently set to. 

### Possible features to come in the future

* HTML UI to query/pick timestamps
* Disk cache
* Logging/history


## Requirements

  * Docker (see below)

  or

  * python3
  * uwsgi (w/ python3 plugin)
  * redis (w/ python3 library)

## Run in Docker

```
$ docker build -t halfmanhalftaco/proxybackmachine:latest .
$ mkdir -p data/redis && chmod 777 data/redis
$ docker run -d -v $PWD/data:/data -p 1080:1080 halfmanhalftaco/proxybackmachine:latest
```

  * or use the `build.sh`, `run.sh`, and `debug.sh` scripts provided.

## Ports

  * 1080: HTTP Proxy
    * to change this, edit `app/uwsgi.ini`

## Optional ports

  * 1081: uwsgi stats
  * 9001: supervisord
  * 6379: redis

