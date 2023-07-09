import os
from werkzeug.wrappers import Request, Response
import json


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)

        if request.headers.get('Authorization') != os.getenv('API_KEY'):
            res = Response(
                json.dumps({'message': 'Authorization failed', 'status': 401}),
                status=401,
                content_type='application/json'
            )
            return res(environ, start_response)

        return self.app(environ, start_response)

