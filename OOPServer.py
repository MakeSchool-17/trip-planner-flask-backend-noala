""" GENERAL IMPORTS """
from functools import wraps


""" FLASK IMPORTS """
from flask import Flask, request, make_response
from flask_restful import Resource, Api


""" FLASK BOILERPLATE """
app = Flask(__name__)
api = Api(app)


""" LOCAL IMPORTS """
from OOPModel import *


# """ DECORATORS """
def require_auth(f):

    @wraps(f)
    def helper(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return ({'error': 'Basic Auth Required.'}, 401, None)
        try:
            user = User(username=auth.username)
        except:
            return ({'error': 'Invalid Auth.'}, 401, None)
        if not user.compare_password(auth.password):
            return ({'error': 'Invalid Auth.'}, 401, None)

        return f(*args, **kwargs)
    return helper


def params(*params):

    def decorator(f):
        def helper(*args, **kwarg):
            json = request.json

            for param in params:
                if param not in json or not json[param]:
                    return ({'error': 'Request requires username and password'}, 400, None)
                kwargs[param] = json[param]

            return f(*args, **kwargs)
    return decorator


# """ IMPLEMENT REST Resource """
class Users(Resource):

    @params('username', 'password')
    def post(self, username=None, password=None):
        user = User()
        user.set('username', username)
        user.set_password(password)
        was_saved = user.save()

        if not was_saved:
            return ({'error': 'Username already in use'}, 400, None)

        return {
            'identifier': user.identifier()
        }

    @require_auth
    def get(self):
        return {}


""" ADD REST RESOURCE TO API """
api.add_resource(Users, '/users/')


# """ API RESPONSE ENCODING """
@api.representation('application/json')
def output_json(data, code, headers=None):
    from json import dumps as stringify
    resp = make_response(stringify(data), code)
    resp.headers.extend(headers or {})
    return resp


# """ START SERVER COMMANDS """
if __name__ == '__main__':
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
