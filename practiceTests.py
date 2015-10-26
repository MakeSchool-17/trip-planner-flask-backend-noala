import practiceServer
import unittest
import json
from pymongo import MongoClient
import base64


def auth_header(username, password):
    credentials = '{0}:{1}'.format(username, password).encode('utf-8')
    encode_login = base64.b64encode(credentials).decode()
    return dict(Authorization="Basic " + encode_login)


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.app = practiceServer.app.test_client()
        # Run app in testing mode to retrieve exceptions and stack traces
        practiceServer.app.config['TESTING'] = True

        # Inject test database into application
        mongo = MongoClient('localhost', 27017)
        db = mongo.test_database
        practiceServer.app.db = db

        # Drop collection (significantly faster than dropping entire db)
        db.drop_collection('user')
        db.drop_collection('trip')

    def test_userdb(self):
        response = self.app.post('/user/',
                                data=json.dumps(
                                dict(username='doge',
                                password='1234')),
                                content_type='application/json')
        responseJSON = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)

        trip_data = dict(trip='africa', waypoints=['egypt', 'ethiopia', 'south africa'])
        response = self.app.post('/trip/',
                                 data=json.dumps(trip_data),
                                 content_type='application/json',
                                 headers=auth_header('doge', '1234'))
        responseJSON = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/user/',
                                headers=auth_header('doge', '1234'))
        responseJSON = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)

    def test_tripdb_auth(self):
        # create new user
        response = self.app.post('/user/',
                                data=json.dumps(
                                dict(username='doge',
                                password='1234')),
                                content_type='application/json')
        responseJSON = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)

        # post new trip with auth
        trip_data = dict(trip='europe', waypoints=['london', 'paris', 'milan'])
        response = self.app.post('/trip/',
                                 data=json.dumps(trip_data),
                                 content_type='application/json',
                                 headers=auth_header('doge', '1234'))
        responseJSON = json.loads(response.data.decode())
        postedObjectID = responseJSON['_id']
        self.assertEqual(response.status_code, 200)
        print(responseJSON)

    # # Trip tests
    # def test_posting_trip(self):
    #     # create new user
    #     response = self.app.post('/user/',
    #                             data=json.dumps(dict(username='doge',
    #                             password='1234')),
    #                             content_type='application/json')
    #     responseJSON = json.loads(response.data.decode())
    #     self.assertEqual(response.status_code, 200)
    #
    #     # post new trip with auth
    #     trip_data = dict(trip='europe', waypoints=['london', 'paris', 'milan'])
    #     response = self.app.post('/trip/',
    #                              data=json.dumps(trip_data),
    #                              content_type='application/json',
    #                              headers=auth_header('doge', '1234'))
    #     responseJSON = json.loads(response.data.decode())
    #     postedObjectID = responseJSON['_id']
    #     self.assertEqual(response.status_code, 200)
    #     print(responseJSON)

        # # import pdb; pdb.set_trace()
        # response = self.app.post('/trip/', data=json.dumps(dict(name="trip",
        #         waypoints=[
        #             dict(
        #                 name="place",
        #                 lat="1234",
        #                 long="4321"),
        #             dict(
        #                 name="place",
        #                 lat="1234",
        #                 long="4321")]
        #     )), content_type='application/json')

        # responseJSON = json.loads(response.data.decode())
        # self.assertEqual(response.status_code, 200)
        # assert 'application/json' in response.content_type
        # assert 'trip' in responseJSON["name"]

    # def test_getting_trip(self):
    #     response = self.app.post('/trip/', data=json.dumps(dict(name="new_trip",
    #             waypoints=[
    #                 dict(
    #                     name="place",
    #                     lat="1234",
    #                     long="4321"),
    #                 dict(
    #                     name="place",
    #                     lat="1234",
    #                     long="4321")]
    #         )), content_type='application/json', headers=auth_header('doge', '1234'))
    #
    #     postResponseJSON = json.loads(response.data.decode())
    #     postedObjectID = postResponseJSON["_id"]
    #
    #     response = self.app.get('/trip/' + postedObjectID, headers=auth_header('doge', '1234'))
    #     responseJSON = json.loads(response.data.decode())
    #
    #     self.assertEqual(response.status_code, 200)
    #     assert 'new_trip' in responseJSON["name"]

    # def test_getting_non_existent_trip(self):
    #     response = self.app.get('/trip/55f0cbb4236f44b7f0e3cb23')
    #     self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
