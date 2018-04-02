import flask
from flask import jsonify, request
from flask_cors import CORS
import os
from pymongo import MongoClient
import requests

ENV = os.environ.get('ENV', 'production')
if ENV == 'test':
    SA_SERVICE_PORT = '31206'
    SA_SERVICE_HOST = '188.166.115.138'
else:
    SA_SERVICE_PORT = '5000'
    SA_SERVICE_HOST = os.environ.get('SA_SERVICE_HOST', 'localhost')

MONGODB_HOST = os.environ.get('MONGODB_HOST', 'localhost')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'tmdata')

app = flask.Flask(__name__)
CORS(app)


def resp(code, data):
    return (jsonify(data), code)


def check_request(request, fields):
    errors = []
    if not request.json:
        errors.append("No JSON sent. Did you forget to set Content-Type header" +
            " to application/json?")
        return errors

    for field in fields:
        if not field['name'] in request.json:
            errors.append('Field "{}" is missing'.format(field['name']))
        else:
            if type(request.json[field['name']]) is not field['type']:
                errors.append('Field "{}" must be {}'.format(field['name'], field['type']))
    return errors


def get_collection():
    try:
        client = MongoClient(MONGODB_HOST, 27017)
    except:
        print("Can't create connection")
        os._exit(1)

    db = client[MONGODB_DATABASE]
    posts = db['posts']
    return posts


def get_polarity(text):
    dict_to_send={'raw_text':text}
    res = requests.post('http://'+SA_SERVICE_HOST+':'+SA_SERVICE_PORT, json=dict_to_send)
    print(res)
    json = res.json()
    return(json['polarity'])


def add_to_database(collection, theme, text, polarity):
    post={'theme':theme, 'text':text, 'polarity':polarity}
    try:
        collection.insert_one(post)
    except:
        print('error in add to mongo')
        os._exit(1)


def get_posts_from_database(collection, theme=None):
    if theme:
        result_cursor = collection.find({'theme':theme})
    else:
        result_cursor = collection.find()
    result = []
    for doc in result_cursor:
        del doc['_id']
        result.append(doc)
    return result


@app.route('/get_env_var', methods=['GET'])
def get_env_var():
    text = 'SA_SERVICE_HOST: {}\n'.format(SA_SERVICE_HOST)
    text += 'MONGODB_HOST: {}\n'.format(MONGODB_HOST)


@app.route('/posts', methods=['POST'])
def add_new_post():
    required_fileds = [
        {'name': 'text', 'type': str},
        {'name': 'theme', 'type': str}
    ]
    errors = check_request(request=request, fields=required_fileds)
    if errors:
        return resp(code=400, data={'status':'error', 'errors':errors})
    
    theme = request.json['theme']
    text = request.json['text']
    polarity = get_polarity(text)
    add_to_database(collection=app.config['collection'], theme=theme, text=text, polarity=polarity)
    return(jsonify({'status': 'ok'}), 200)


@app.route('/posts/<theme>', methods=['GET'])
def get_posts_by_theme(theme):
    result = get_posts_from_database(collection=app.config['collection'], theme=theme)
    return(jsonify({'status':'ok', 'result':result}), 200)


def main():
    app.config['collection'] = get_collection()
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()