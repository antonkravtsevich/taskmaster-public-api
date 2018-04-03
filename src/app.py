import flask
from flask import jsonify, request
from flask_cors import CORS
import os
from pymongo import MongoClient
from pymongo import DESCENDING as DESC
import requests
from datetime import datetime
import pandas as pd

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
startTime = datetime.now()


def resp(code, data):
    return (jsonify(data), code)


# using dict of required fields and their types to validate request
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
                errors.append('Field "{}" must be {}, current: {}'.format(field['name'], 
                                                                          field['type'], 
                                                                          type(request.json[field['name']])))
    return errors


# get tweets collection from database
def get_collection():
    print('Create database connection...')
    try:
        client = MongoClient(MONGODB_HOST, 27017)
    except:
        print("Can't create connection")
        os._exit(1)

    db = client[MONGODB_DATABASE]
    posts = db['posts']
    print('Successfully connect to database')
    return posts


# request polarity count for sentimental analyzer service
def get_polarity(text):
    dict_to_send={'raw_text':text}
    res = requests.post('http://'+SA_SERVICE_HOST+':'+SA_SERVICE_PORT, json=dict_to_send)
    print(res)
    json = res.json()
    return(json['polarity'])


# add new record to database
def add_to_database(collection, timestamp, text, polarity):
    post={'timestamp':timestamp, 'text':text, 'polarity':polarity}
    try:
        collection.insert_one(post)
    except Exception as e:
        print('error in add to mongo: str(e)')
        os._exit(1)


# get posts from database (using theme)
def get_posts_from_database(collection, theme=None):
    if theme:
        low_theme = str(theme).lower()
        result_cursor = collection.find({'text':{'$regex':low_theme, '$options':'i'}})
    else:
        result_cursor = collection.find()
    result = []
    for doc in result_cursor:
        del doc['_id']
        result.append(doc)
    return result


# get polarity variables of theme
def get_polarity_from_database(collection, theme):
    low_theme = str(theme).lower()
    result_cursor = collection.find({'text':{'$regex':low_theme, '$options':'i'}}).sort([('timestamp', DESC)]).limit(1000)
    
    df = pd.DataFrame(list(result_cursor))
    df.sort_values('timestamp', inplase=True)
    df['polarity_smoothed'] = df['polarity'].rolling(int(len(df)/5)).mean()

    polarity_mean = df['polarity'].mean()
    positive_tweets_count=len(df[df['polarity']>0])
    negative_tweets_count=len(df[df['polarity']<0])
    neutral_tweets_count=len(df[df['polarity']==0.0])
    polarity=df['polarity_smoothed'].tolist()

    result={
        'polarity_mean':polarity_mean,
        'neutral_tweets_count':neutral_tweets_count,
        'positive_tweets_count':positive_tweets_count,
        'negative_tweets_count':negative_tweets_count,
        'polarity':polarity
    }
    return(result)


@app.route('/status', methods=['GET'])
def get_env_var():
    currTime = datetime.now()
    text = 'Uptime: {}<br><br>'.format(currTime - startTime)
    text += 'SA_SERVICE_HOST: {}<br>'.format(SA_SERVICE_HOST)
    text += 'MONGODB_HOST: {}'.format(MONGODB_HOST)
    return(text, 200)


@app.route('/posts', methods=['POST'])
def add_new_post():
    required_fileds = [
        {'name': 'text', 'type': str},
        {'name': 'timestamp', 'type': str}
    ]
    errors = check_request(request=request, fields=required_fileds)
    if errors:
        return resp(code=400, data={'status':'error', 'errors':errors})
    
    timestamp = request.json['timestamp']
    text = request.json['text']
    polarity = get_polarity(text)
    add_to_database(collection=app.config['collection'], timestamp=timestamp, text=text, polarity=polarity)
    return(jsonify({'status': 'ok'}), 200)


@app.route('/posts', methods=['GET'])
def get_posts_by_theme():
    theme = flask.request.args.get('theme', '')
    theme = theme.replace('+', ' ')
    result = get_posts_from_database(collection=app.config['collection'], theme=theme)
    return(jsonify({'status':'ok', 'result':result}), 200)


@app.route('/polarity', methods=['GET'])
def get_polarity_by_theme():
    theme = flask.request.args.get('theme', '')
    theme = theme.replace('+', ' ')
    result = get_polarity_from_database(collection=app.config['collection'], theme=theme)
    return(jsonify({'status':'ok', 'result':result}), 200)


def main():
    if ENV=="test":
        print('Test environment')
    app.config['collection'] = get_collection()
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()