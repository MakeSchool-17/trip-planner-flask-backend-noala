# """ ENCRYPTION IMPORTS """
import bcrypt


# """ PYMONGO IMPORTS """
from pymongo import MongoClient


# """ PYMONGO SETUP """
mongo = MongoClient('localhost', 27017)
db = mongo.develop_database


# """ BSON IMPORTS """
from bson.objectid import ObjectId


# """ EXCEPTIONS """
class NullDocumentException(Exception):
    pass


class DBModel(object):

    def __init__(self, identifier=None, rawdata=None):

        self.is_saved = False
        if identifier:
            self._queryload({'_id': ObjectId(identifier)})
        elif rawdata:
            self._rawload(rawdata)
        else:
            self.data = {}

    def _rawload(self, data):

        self.is_saved = True
        self.data = data

    def _queryload(self, query):

        collection = self._collection()
        entity = collection.find_one(query)
        if not entity:
            raise NullDocumentException()
        self._rawload(entity)

    @classmethod
    def _collection(cls):

        return db[cls.__name__]

    def save(self):

        if self.is_saved:
            self._update()
        else:
            self._insert()
        return True

    def _update(self):

        collection = self._collection()
        collection.update_one({
            '_id': self.data['_id']
        }, {
            '$set': self.data
        })

    def _insert(self):

        collection = self._collection()
        collection.insert_one(self.data)
        self.is_saved = True

    def set(self, key, value):

        self.data[key] = value

    def get(self, key):

        return self.data[key]

    def identifier(self):

        return str(self.get('_id'))

    @classmethod
    def fetch(cls, query):

        collection = cls._collection()
        entities = collection.find(query)
        return [cls(rawdata=entity) for entity in entities]


class User(DBModel):

    BCRYPT_ROUNDS = 12

    def __init__(self, *args, username=None, **kwargs):

        super(User, self).__init__(*args, **kwargs)
        if username:
            self._queryload({'username': username})

    def set_password(self, password):

        encodedpassword = password.encode('utf-8')
        hashed = bcrypt.hashpw(encodedpassword, bcrypt.gensalt(self.BCRYPT_ROUNDS))
        self.set('password', hashed)

    def compare_password(self, password):

        encodedpassword = password.encode('utf-8')
        return bcrypt.hashpw(encodedpassword, self.get('password')) == self.get('password')

    def save(self):

        if not self.is_saved:
            query = self.fetch({'username': self.get('username')})
            if len(query) > 0:
                return False
        return super(User, self).save()
