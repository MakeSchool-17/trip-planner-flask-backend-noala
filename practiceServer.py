from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
from bcrypt import hashpw, gensalt
from functools import wraps

# # Basic Setup # #
# assign var app to new flask instance
app = Flask(__name__)
# establish connection to mongodb run locally
mongo = MongoClient('localhost', 27017)
# specify database to use
app.db = mongo.develop_database
# create instance of flask_restful API
api = Api(app)

app.bcrypt_rounds = 12


def hash_pw(password, salt=None):
    salt = gensalt(app.bcrypt_rounds)
    encoded_pass = password.encode(encoding='UTF-8', errors='strict')
    return hashpw(encoded_pass, salt)


# User Auth code
def check_auth(username, password):
    user_collection = app.db.user
    user = user_collection.find_one({'username': username})
    user_password = user['password']
    try:
        return hash_pw(password, user_password)
    except KeyError:
        return False

# def check_auth(username, password):
#     user_db = app.db.users
#     find_username = user_db.find_one({'username': username})
#     if find_username:
#         db_password = find_username['password']
#         encode_pass = password.encode('utf-8')
#         return bcrypt.hashpw(encode_pass, db_password) == db_password


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)
            resp.status_code = 401
            return resp

        return f(*args, **kwargs)
    return decorated


class Trip(Resource):
    def post(self):
        trip_info = request.json
        trip_collection = app.db.trip
        result = trip_collection.insert_one(trip_info)
        post_info = trip_collection.find_one(
            {'_id': ObjectId(result.inserted_id)})
        return post_info

    @requires_auth
    def get(self, trip_id=None):
        trip_collection = app.db.Trip
        get_info = trip_collection.find_one(
            {'_id': ObjectId(trip_id)})
        if get_info is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return get_info

    def put(self, trip_id):
        trip_info = request.json
        trip_collection = app.db.trip
        update_info = trip_collection.update_one(
            {'_id': ObjectId(trip_id)}, {'$set': trip_info})

        if update_info is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return update_info

    def delete(self, trip_id):
        trip_collection = app.db.trip
        delete_me = trip_collection.find_one(
            {'_id': ObjectId(trip_id)})
        trip_collection.delete_one(delete_me)

        if delete_me is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return delete_me


class User(Resource):
    app.bcrypt_rounds = 12

    def post(self):
        user_info = request.json
        user_collection = app.db.user
        freshpw = user_info["password"]
        user_info['password'] = hash_pw(freshpw)
        insert_user = user_collection.insert_one(user_info)
        post_info = user_collection.find_one(
            {'_id': ObjectId(insert_user.inserted_id)})
        # decode byte to str
        post_info['password'] = post_info['password'].decode('utf-8')
        return post_info

    @requires_auth
    def get(self):
        username = request.authorization.username
        user_collection = app.db.user
        retrieve_user = user_collection.find_one({'username': username})
        if not retrieve_user:
            # return error response
            response = jsonify(data=[])
            response.status_code = 404
            return response
        return {
            'username': retrieve_user['username']
        }

    @requires_auth
    def put(self):
        username = request.authorization.username
        user_info = request.json
        user_collection = app.db.user
        update_user = user_collection.update_one(
            {'username': username}, {'$set': user_info})
        return update_user

    @requires_auth
    def delete(self):
        username = request.authorization.username
        user_collection = app.db.user
        retrieve_user = user_collection.find_one(
            {'username': username})
        user_collection.delete_one(retrieve_user)
        return retrieve_user


# Add REST resource to API
api.add_resource(Trip, '/trip/', '/trip/<string:trip_id>', endpoint='trip')
api.add_resource(User, '/user/', endpoint='user')


# provide a custom JSON serializer for flaks_restful
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
