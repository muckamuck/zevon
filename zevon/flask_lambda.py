import sys
import json
import logging
import base64

from zevon.sample_event import sample

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from flask import Flask

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

from werkzeug.wrappers import BaseRequest

OCTET_STREAM = 'application/octet-stream'
logger = logging.getLogger(__name__)


def make_environ(event):
    logger.info(json.dumps(event, indent=2))
    environ = {}

    for hdr_name, hdr_value in event['headers'].items():
        hdr_name = hdr_name.replace('-', '_').upper()
        if hdr_name in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
            environ[hdr_name] = hdr_value
            continue

        http_hdr_name = 'HTTP_{}'.format(hdr_name)
        environ[http_hdr_name] = hdr_value

    is_encoded = event.get('isBase64Encoded', False)

    wrk = event.get('body', '')
    if is_encoded and wrk:
        event_body = base64.b64decode(wrk).decode()
    else:
        event_body = wrk

    environ['REQUEST_METHOD'] = event['httpMethod']
    environ['PATH_INFO'] = event['path']
    environ['REMOTE_ADDR'] = event['requestContext']['identity']['sourceIp']
    environ['HOST'] = '%(HTTP_HOST)s:%(HTTP_X_FORWARDED_PORT)s' % environ
    environ['SCRIPT_NAME'] = ''
    environ['SERVER_PORT'] = environ['HTTP_X_FORWARDED_PORT']
    environ['SERVER_PROTOCOL'] = 'HTTP/1.1'
    environ['wsgi.url_scheme'] = environ['HTTP_X_FORWARDED_PROTO']
    environ['wsgi.input'] = StringIO(event_body)
    environ['wsgi.version'] = (1, 0)
    environ['wsgi.errors'] = sys.stderr
    environ['wsgi.multithread'] = False
    environ['wsgi.run_once'] = True
    environ['wsgi.multiprocess'] = False

    query_string = event['queryStringParameters']
    if query_string:
        environ['QUERY_STRING'] = urlencode(query_string)
    else:
        environ['QUERY_STRING'] = ''

    if event_body:
        environ['CONTENT_LENGTH'] = str(len(event_body))
    else:
        environ['CONTENT_LENGTH'] = ''

    BaseRequest(environ)

    return environ


class Response(object):
    def __init__(self):
        self.status = None
        self.response_headers = None

    def start_response(self, status, response_headers, exc_info=None):
        self.status = int(status[:3])
        self.response_headers = dict(response_headers)


class FlaskLambda(Flask):
    def __call__(self, event, context):
        logger.debug(json.dumps(event))
        if 'httpMethod' not in event:
            # In this "context" `event` is `environ` and
            # `context` is `start_response`, meaning the request didn't
            # occur via API Gateway and Lambda
            return super(FlaskLambda, self).__call__(event, context)

        response = Response()

        encoded_body = next(self.wsgi_app(
            make_environ(event),
            response.start_response
        ))

        body = encoded_body.decode('utf-8')
        logger.debug(f'encoded_body={encoded_body}')
        logger.debug(f'body={body}')

        content_type = response.response_headers.get('Content-Type')
        if content_type.startswith('image') or content_type == OCTET_STREAM:
            wrk = {
                'statusCode': response.status,
                'headers': response.response_headers,
                'body': body,
                'isBase64Encoded': True
            }

            the_answer = json.dumps(wrk)
            logger.info(f'the_answer={the_answer}')
            return wrk
        else:
            return {
                'statusCode': response.status,
                'headers': response.response_headers,
                'body': body
            }


if __name__ == '__main__':
    make_environ(sample)
