import hash_functions
from werkzeug.security import safe_str_cmp
from bson.objectid import ObjectId


class Clients:

    def __init__(self, dbworker):
        self.clients = dbworker.get_clients_collection()

    def registration(self, client_name, password):
        hash_pass = hash_functions.get_hash(password)
        new_client = {'client_name': client_name, 'password': hash_pass}
        try:
            self.clients.insert_one(new_client)
        except Exception as e:
            print('error in add to mongo: {}'.format(str(e)))
            return('Registration error')
        return(None)

    def get_client_by_name(self, client_name):
        client_cursor = self.clients.find_one({'client_name': client_name})
        return client_cursor

    def authenticate(self, client_name, password):
        client = self.get_client_by_name(client_name)
        if (client):
            hash_pass = hash_functions.get_hash(password)
            if safe_str_cmp(client['password'], hash_pass):
                client['id'] = str(client['_id'])
                del client['_id']
                return client

    def identity(self, payload):
        client_id = payload['_id']
        client = self.clients.find_one({'_id': ObjectId(client_id)})
        client['id'] = str(client['_id'])
        del client['_id']
        print(client)
        return client
