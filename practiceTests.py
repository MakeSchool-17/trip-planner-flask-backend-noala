import practiceServer
import unittest
import json
from pymongo import MongoClient


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
        db.drop_collection('trip')

    # Trip tests
    def test_posting_trip(self):
        # import pdb; pdb.set_trace()
        response = self.app.post('/trip/', data=json.dumps(dict(name="trip",
                waypoints=[
                    dict(
                        name="place",
                        lat="1234",
                        long="4321"),
                    dict(
                        name="place",
                        lat="1234",
                        long="4321")]
            )), content_type='application/json')

        responseJSON = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'trip' in responseJSON["name"]

    def test_getting_trip(self):
        response = self.app.post('/trip/', data=json.dumps(dict(name="new_trip",
                waypoints=[
                    dict(
                        name="place",
                        lat="1234",
                        long="4321"),
                    dict(
                        name="place",
                        lat="1234",
                        long="4321")]
            )), content_type='application/json')

        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON["_id"]

        response = self.app.get('/trip/' + postedObjectID)
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'new_trip' in responseJSON["name"]

    def test_getting_non_existent_trip(self):
        response = self.app.get('/trip/55f0cbb4236f44b7f0e3cb23')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
