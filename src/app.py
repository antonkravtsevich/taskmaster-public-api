from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)
SA_SERVICE_HOST = os.environ.get('SA_SERVICE_HOST', 'localhost')
MONGODB_HOST = os.environ.get('MONGODB_HOST', 'localhost')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'tmdata')

#create connection
try:
    client = MongoClient(MONGODB_HOST, 27017)
except:
    print("Can't create connection")
    os._exit(1)

db = client[MONGODB_DATABASE]
posts = db['posts']


def get_polarity(text):
    dict_to_send={'raw_text':text}
    res = requests.post('http://'+SA_SERVICE_HOST+':5000', json=dict_to_send)
    print(res)
    json = res.json()
    return(json['polarity'])


# REMOVE THAT AFTER TEST!!!
@app.route('/get_env_var', methods=['GET'])
def get_env_var():
    text = 'SA_SERVICE_HOST: {}\n'.format(SA_SERVICE_HOST)
    text += 'MONGODB_HOST: {}\n'.format(MONGODB_HOST)


@app.route('/posts', methods=['POST'])
def add_new_post():
    json = request.get_json(silent=True)
    theme = json['theme']
    text = json['text']
    polarity = get_polarity(text)
    post={'theme':theme, 'text':text, 'polarity':polarity}

    print('Theme: {}\nText: {}\nPolarity: {}'.format(theme, text, polarity))
    try:
        post_id = posts.insert_one(post).inserted_id
    except:
        print('error in add to mongo')
        os._exit(1)
    return(jsonify({'status': 'ok'}), 200)


@app.route('/posts/<theme>', methods=['GET'])
def get_posts_by_theme(theme):
    result_cursor = posts.find({'theme':theme})
    result = []
    for doc in result_cursor:
        del doc['_id']
        result.append(doc)
    print(result)
    return(jsonify({'status':'ok', 'result':result}), 200)


def main():
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
