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

    # User Tests
    def test_posting_user(self):
        # import pdb; pdb.set_trace()
        response = self.app.post(
            '/user/',
            data=json.dumps(dict(
                username="doge",
                password="1234"
            )),
            content_type='application/json')

        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'doge' in responseJSON["username"]

    # def test_getting_non_existent_user(self):
    #     response = self.app.get('/user/55f0cbb4236f44b7f0e3cb23')
    #     self.assertEqual(response.status_code, 404)

    def test_getting_user(self):
        response = self.app.post(
            '/user/',
            data=json.dumps(dict(
                username='dogey',
                password='1234'
            )),
            content_type='application/json', headers=auth_header('dogey', '1234'))

        response = self.app.get('/user/', headers=auth_header('dogey', '1234'))
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'dogey' in responseJSON["username"]


if __name__ == '__main__':
    unittest.main()
