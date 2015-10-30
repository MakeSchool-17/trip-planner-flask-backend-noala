import bcrypt
from flask import Flask, request, make_response
from flask_restful import Resource, Api
from pymongo import MongoClient
from utils.mongo_json_encoder import JSONEncoder
from bson.objectid import ObjectId
from functools import wraps

app = Flask(__name__)
mongo = MongoClient('localhost', 27017)
app.db = mongo.develop_database
app.bcrypt_rounds = 12
api = Api(app)


def check_auth(username, password):
    user_collection = app.db.users
    user = user_collection.find_one({'username': username})

    if user is None:
        return False
    else:
        # check if the hash we generate based on auth matches stored hash
        encodedPassword = password.encode('utf-8')
        if bcrypt.hashpw(encodedPassword,
                         user['password']) == user['password']:
            return True
        else:
            return False


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return ({'error': 'Basic Auth Required.'}, 401, None)
        return f(*args, **kwargs)
    return decorated


class User(Resource):

    def post(self):
        if (request.json['username'] is None
                or request.json['password'] is None):
                return ({'error':  'Request requires username and password'},
                        400,
                        None)

        user_collection = app.db.users
        user = user_collection.find_one({'username': request.json['username']})

        if user is not None:
            return ({'error': 'Username already in use'}, 400, None)
        else:
            encodedPassword = request.json['password'].encode('utf-8')
            hashed = bcrypt.hashpw(
                encodedPassword, bcrypt.gensalt(app.bcrypt_rounds))
            request.json['password'] = hashed
            user_collection.insert_one(request.json)

    @requires_auth
    def get(self):
        return (None, 200, None)


class Trip(Resource):

    @requires_auth
    def get(self, trip_id=None):
        if trip_id is None:
            trip_collection = app.db.trips
            trips = list(trip_collection.find(
                {'user': request.authorization.username}))
            return trips
        else:
            trip_collection = app.db.trips
            trip = trip_collection.find_one(
                {'_id': ObjectId(trip_id),
                 'user': request.authorization.username})

            if trip is None:
                # Flask allows us to return tuple in form
                # (response, status, headers)
                return (None, 404, None)
            else:
                return trip

    @requires_auth
    def post(self):
        new_trip = request.json
        new_trip['user'] = request.authorization.username
        trip_collection = app.db.trips
        result = trip_collection.insert_one(request.json)

        trip = trip_collection.find_one(result.inserted_id)

        return (trip, 201, None)

    @requires_auth
    def put(self, trip_id):
        new_trip = request.json
        new_trip['user'] = request.authorization.username
        trip_collection = app.db.trips

        # remove _id since we can't update it and would need to
        # transform it into an ObjectId
        del request.json['_id']
        trip_collection.update_one({'_id': ObjectId(trip_id),
                                    'user': request.authorization.username},
                                   {'$set': request.json})
        trip = trip_collection.find_one(ObjectId(trip_id))

        return trip

    @requires_auth
    def delete(self, trip_id):
        trip_collection = app.db.trips
        trip_collection.delete_one(
            {'_id': ObjectId(trip_id),
             'user': request.authorization.username}
        )

        return {"tripIdentifier": trip_id}

api.add_resource(Trip, '/trip/', '/trip/<string:trip_id>')
api.add_resource(User, '/user/')


# provide a custom JSON serializer for flaks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request
    # related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
