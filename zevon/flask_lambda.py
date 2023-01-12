import sys
import json
import logging
import base64
import datetime
import time
from io import StringIO
from urllib.parse import urlencode

from zevon.sample_event import sample
from flask import Flask


from werkzeug.wrappers import Request

OCTET_STREAM = 'application/octet-stream'

binary_things = [
    'image',
    'font'
]

init_time = int(time.time())
logger = logging.getLogger(__name__)


def json_converter(o):
    '''
    Helper thing to convert dates for JSON modulet.

    Args:
        o - the thing to dump as string.

    Returns:
        if an instance of datetime the a string else None
    '''
    if isinstance(o, datetime.datetime):
        return o.__str__()
    elif isinstance(o, StringIO):
        return o.getvalue()

    return None


def create_request_data(event):
    request_data = {}
    try:
        request_data['id'] = event.get('requestContext', {}).get('requestId', None)
        request_data['requestTimeEpoch'] = event.get('requestContext', {}).get('requestTimeEpoch', None)
        request_data['initTimeEpoch'] = init_time
        request_data['lambdaAge'] = int(time.time()) - init_time
        request_data['sourceIp'] = event.get('requestContext', {}).get('identity', {}).get('sourceIp', None)
        request_data['userArn'] = event.get('requestContext', {}).get('identity', {}).get('userArn', None)
        request_data['userAgent'] = event.get('requestContext', {}).get('identity', {}).get('userAgent', None)
    except Exception as ruh_roh_shaggy:
        logger.error(ruh_roh_shaggy, exc_info=False)

    return request_data


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

    try:
        Request(environ)
        return environ
    except Exception as wtf:
        logger.error(wtf, exc_info=True)
        return None


class Response(object):
    def __init__(self):
        self.status = None
        self.response_headers = None

    def start_response(self, status, response_headers, exc_info=None):
        self.status = int(status[:3])
        self.response_headers = dict(response_headers)


class FlaskLambda(Flask):
    def __call__(self, event, context):
        self.request_data = create_request_data(event)
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
        content_family = content_type.split('/')[0]
        if content_family in binary_things or content_type == OCTET_STREAM:
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
