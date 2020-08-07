#!/usr/bin/env python3
"""
###
### proxybackmachine
###     an HTTP proxy to the past
###        (c) 2020 halfmanhalftaco
###
"""

import json
from redis import Redis

from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

DEFAULT_DATE = '19990601'

def timestamp_query(url, target_date):
    """queries for nearest timestamp to target date from archive.org"""
    parsed_url = urlparse(url)

    # check timestamp cache
    ts_cached = Redis().get(f"{parsed_url.netloc}{parsed_url.path}:{target_date}")
    if ts_cached:
        return ts_cached.decode('utf-8')

    # cache miss, ask archive.org
    base_url = 'https://web.archive.org/wayback/available?url='
    req_url = f"{base_url}{parsed_url.netloc}{parsed_url.path}&timestamp={target_date}"

    try:
        req = urlopen(req_url)
    except (HTTPError, URLError):
        return 'NONE!'

    result = req.read()
    match = json.loads(result)
    try:
        timestamp = match['archived_snapshots']['closest']['timestamp']
    except KeyError:
        print('no snapshot available', match)
        timestamp = 'NONE!'

    # populate cache
    Redis().mset({f"{parsed_url.netloc}{parsed_url.path}:{target_date}": timestamp})

    return timestamp

def wayback_fetch(orig_url, timestamp):
    """fetches content from archive.org for given url and timestamp"""
    url = 'https://web.archive.org/web/' + timestamp + 'id_/' + orig_url
    print(url)
    status = '200 OK'

    try:
        req = urlopen(url)
    except HTTPError as err:
        print(err)
        status = f"{err.code} {err.reason}"
        return error_page(status)

    raw_headers = req.info()
    headers = []

    for hdr in raw_headers.items():
        hname = hdr[0]
        if hname.startswith('X-Archive-Orig-'):
            name = hname.replace('X-Archive-Orig-', '')
            if name in ['Connection', 'Keep-Alive', 'Transfer-Encoding']:
                continue
            headers.append((name, hdr[1]))
        elif hname == 'Content-Type':
            headers.append(hdr)

    return status, headers, req.read()


def fix_url(url):
    """
    Massage url from client, remove session ids,
    fix things that don't work on the wayback machine, etc.
    """
    parsed_url = urlparse(url)
    redir = False

    # remove java-style session IDs
    sid = url.find(';$sessionid$')
    if sid > -1:
        url = url[:sid]
        redir = True

    # fix yahoo redirects circa 2001
    if parsed_url.netloc == "srd.yahoo.com" and '*' in parsed_url.path:
        url = url.split('*')[1]
        redir = True

    return url, redir

def wayback_query(url, date):
    """fix URL, get most relevant timestamp and fetch data from archive"""
    url, redir = fix_url(url)
    if redir:
        return redirect(url)

    timestamp = timestamp_query(url, date)
    if timestamp == 'NONE!':
        return error_page('404 Not Found')

    return wayback_fetch(url, timestamp)

def redirect(url, code='302 Found'):
    """returns an HTTP redirect"""
    headers = [('Location', url)]
    return code, headers, ''.encode()

def error_page(code):
    """returns a generic HTTP error page"""
    return code, [('Content-Type', 'text/plain')], code.encode()

def status_page(environ):
    """
    outputs some debug information and allows setting the proxy date
    from the client machine.
    """
    status = '200 OK'
    headers = [('Content-Type', 'text/plain;charset=utf-8')]
    addr = environ['REMOTE_ADDR']

    client_date = proxy_date(addr)
    output = 'Proxybackmachine (c) 2020 halfmanhalftaco\n\n'
    if client_date:
        output += f"Current proxy date for {addr}: {client_date}\n\n"

    output += 'Parsed REQUEST_URI:\n'
    parsed_url = urlparse(environ['REQUEST_URI'])
    output += str(parsed_url) + '\n\n'

    if parsed_url.query:
        query = parse_qs(parsed_url.query)
        output += 'Parsed query string: \n\n'
        for k in query:
            output += f"{k}: {query[k][0]}\n"
        output += '\n'

        if 'date' in query:
            target_date = query['date'][0]
            Redis().mset({f"wayback_date:{addr}": target_date})
            output += f"Wayback date set to {target_date}\n"

    output += 'WSGI Environment:\n\n'
    for key in environ.keys():
        output += f"{key}: {environ[key]}\n"

    return status, headers, output.encode()

def proxy_date(addr):
    """query redis for client's proxy date or set it to default"""
    date = Redis().get(f"wayback_date:{addr}")
    if not date:
        date = DEFAULT_DATE
        Redis().mset({f"wayback_date:{addr}": date})
    else:
        date = date.decode('utf-8')
    return date

def application(environ, start_response):
    """
    main WSGI request handler
    """
    method = environ['REQUEST_METHOD']
    path = environ['REQUEST_URI']
    remote = environ['REMOTE_ADDR']

    date = proxy_date(remote)

    if path.startswith('http://') and method == 'GET':
        parsed_url = urlparse(path)
        if parsed_url.netloc == "proxy" or parsed_url.netloc == 'www.proxyback.com':
            status, headers, output = status_page(environ)
        else:
            status, headers, output = wayback_query(path, date)
    elif method == 'CONNECT':
        status, headers, output = error_page('400 Bad Request')
    else:
        status, headers, output = status_page(environ)

    start_response(status, headers)
    return [output]
