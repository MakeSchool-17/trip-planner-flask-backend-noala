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
    """
    ' PURPOSE
    ' General purpose database storage class.
    ' May be extended to provide additional functionality.
    ' NOTES
    ' 1. MongoDB collection based on class (or extended class) name.
    """

    def __init__(self, identifier=None, rawdata=None):
        """
        ' PURPOSE
        '   Constructor for DBModel. May create a new DBModel with no
        '   parameters, thus an unsaved document. With an identifier which
        '   is used to load a document into the model. Or with rawdata already
        '   fetched from the MongoDB database.
        ' PARAMETERS
        '   optional <str identifier>
        '   optional <dict rawdata>
        ' RETURNS
        '   <DBModel model>
        """
        self.is_saved = False
        if identifier:
            self._queryload({'_id': ObjectId(identifier)})
        elif rawdata:
            self._rawload(rawdata)
        else:
            self.data = {}

    def _rawload(self, data):
        """
        ' PURPOSE
        '   Private method which loads the model from raw document data
        ' PARAMETERS
        '   <dict data>
        ' RETURNS
        '   None
        """
        self.is_saved = True
        self.data = data

    def _queryload(self, query):
        """
        ' PURPOSE
        '   Using a bson query dictionary, load a document's data into the model.
        ' PARAMETERS
        '   <dict query>
        ' RETURNS
        '   None
        ' EXCEPTIONS
        '   NullDocumentException
        """
        collection = self._collection()
        entity = collection.find_one(query)
        if not entity:
            raise NullDocumentException()
        self._rawload(entity)

    @classmethod
    def _collection(cls):
        """
        ' PURPOSE
        '   Returns a MongoDB collection for this model
        ' PARAMETERS
        '   None
        ' RETURNS
        '   None
        """
        return db[cls.__name__]

    def save(self):
        """
        ' PURPOSE
        '   Saves the current model's data. Either updating old data if this model
        '   was initialized with a pre-existing document, or inserting new data if not.
        ' PARAMETERS
        '   None
        ' RETURNS
        '   <bool success> True if saved, False if not.
        """
        if self.is_saved:
            self._update()
        else:
            self._insert()
        return True

    def _update(self):
        """
        ' PURPOSE
        '   Private method to update the current model's document.
        ' PARAMETERS
        '   None
        ' RETURNS
        '   None
        """
        collection = self._collection()
        collection.update_one({
            '_id': self.data['_id']
        }, {
            '$set': self.data
        })

    def _insert(self):
        """
        ' PURPOSE
        '   Private method to insert a new document.
        ' PARAMETERS
        '   None
        ' RETURNS
        '   None
        """
        collection = self._collection()
        collection.insert_one(self.data)
        self.is_saved = True

    def set(self, key, value):
        """
        ' PURPOSE
        '   Adds a new key and value pair to the current model's document
        ' PARAMETERS
        '   <str key>
        '   <object value>
        ' RETURNS
        '   None
        """
        self.data[key] = value

    def get(self, key):
        """
        ' PURPOSE
        '   Retrieves the value associated with the given key from the current
        '   document.
        ' PARAMETERS
        '   <str key>
        ' RETURNS
        '   <object value>
        """
        return self.data[key]

    def identifier(self):
        """
        ' PURPOSE
        '   Returns the identifier of the current document.
        ' PARAMETERS
        '   None
        ' RETURNS
        '   <str identifier>
        """
        return str(self.get('_id'))

    @classmethod
    def fetch(cls, query):
        """
        ' PURPOSE
        '   Performs a bson query on the given data model.
        ' PARAMETERS
        '   <dict query>
        ' RETURNS
        '   [DBModel model1, model2, ... modelN]
        """
        collection = cls._collection()
        entities = collection.find(query)
        return [cls(rawdata=entity) for entity in entities]


class User(DBModel):
    """
    ' PURPOSE
    '   Extension of DBModel to implement user data-storage.
    """

    """ CLASS CONSTANTS """
    BCRYPT_ROUNDS = 12

    def __init__(self, *args, username=None, **kwargs):
        """
        ' PURPOSE
        '   Initializes the current model using DBModel's inherited
        '   __init__ function with the added ability to initialize based
        '   on username.
        ' PARAMETERS
        '   *args
        '   <str username>
        '   **kwargs
        ' RETURNS
        '   <User extends DBModel user_model>
        """
        super(User, self).__init__(*args, **kwargs)
        if username:
            self._queryload({'username': username})

    def set_password(self, password):
        """
        ' PURPOSE
        '   Ecnrypts and sets the provided password
        ' PARAMETERS
        '   <str password>
        ' RETURNS
        '   None
        ' NOTES
        '   1. Uses bcrypt library
        """
        encodedpassword = password.encode('utf-8')
        hashed = bcrypt.hashpw(encodedpassword, bcrypt.gensalt(self.BCRYPT_ROUNDS))
        self.set('password', hashed)

    def compare_password(self, password):
        """
        ' PURPOSE
        '   Given a password, compare it to the saved password.
        ' PARAMETERS
        '   <str password>
        ' RETURNS
        '   <bool is_same> True if passwords match, False if not.
        """
        encodedpassword = password.encode('utf-8')
        return bcrypt.hashpw(encodedpassword, self.get('password')) == self.get('password')

    def save(self):
        """
        ' PURPOSE
        '   Saves the current model using DBModel's inherited save method
        '   with the added functionality of rejecting a username that already
        '   exists in the database if this model has not been loaded from an
        '   existing document.
        ' PARAMETERS
        '   None
        ' RETURNS
        '   <bool success> True if saved, False if not.
        """
        if not self.is_saved:
            query = self.fetch({'username': self.get('username')})
            if len(query) > 0:
                return False
        return super(User, self).save()
