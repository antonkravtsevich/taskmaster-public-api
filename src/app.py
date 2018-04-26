from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity
)
from db_worker import DBWorker
from clients import Clients
from tm import ThematicModeller
from sa import SentimentalAnalyzer
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'ephch5a6qd5XeRubD'

app.config['JWT_SECRET_KEY'] = 'ephch5a6qd5XeRubD'
jwt = JWTManager(app)

ENV = os.environ.get('ENV', 'production')
if ENV == 'test':
    SA_SERVICE_HOST = '188.166.115.138'
    SA_SERVICE_PORT = 31206
    TM_SERVICE_HOST = '188.166.115.138'
    TM_SERVICE_PORT = 32356
    MONGODB_HOST = '188.166.115.138'
    MONGODB_PORT = 31178
else:
    SA_SERVICE_HOST = os.environ.get('SA_SERVICE_HOST', 'localhost')
    SA_SERVICE_PORT = 5000
    TM_SERVICE_HOST = os.environ.get('TM_SERVICE_HOST', 'localhost')
    TM_SERVICE_PORT = 5001
    MONGODB_HOST = os.environ.get('MONGODB_HOST', 'localhost')
    MONGODB_PORT = 27017
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'tmdata')

db = DBWorker('localhost', 27017, 'taskmaster')
clients = Clients(db)
startTime = datetime.now()

tm = ThematicModeller(host=TM_SERVICE_HOST, port=TM_SERVICE_PORT)
sa = SentimentalAnalyzer(host=SA_SERVICE_HOST, port=SA_SERVICE_PORT)


# using dict of required fields and their types to validate request
def check_request(request, fields):
    errors = []
    if not request.json:
        errors.append(
            'No JSON sent. ' +
            'Did you forget to set Content-Type header' +
            ' to application/json?'
        )
        return errors

    for field in fields:
        if not field['name'] in request.json:
            errors.append('Field "{}" is missing'.format(field['name']))
        else:
            if type(request.json[field['name']]) is not field['type']:
                errors.append(
                    'Field "{}" must be {}, current: {}'
                    .format(
                        field['name'],
                        field['type'],
                        type(request.json[field['name']])
                    )
                )
    return errors


@app.route('/auth', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    client = clients.authenticate(username, password)
    if not client:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@app.route('/test_auth', methods=['GET'])
@jwt_required
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


# create response
def resp(code, data):
    return (jsonify(data), code)


@app.route('/add_post', methods=['POST'])
def add_post():
    required_fileds = [
        {'name': 'post_id', 'type': str},
        {'name': 'text', 'type': str}
    ]
    errors = check_request(request=request, fields=required_fileds)
    if errors:
        return resp(code=400, data={'status': 'error', 'errors': errors})

    post_id = request.json['post_id']
    text = request.json['text']
    post_themes = tm.get_themes(text)
    result = db.add_new_post(post_id=post_id, post_themes=post_themes)
    if result:
        return resp(data={'status': 'error', 'error': result}, code=404)
    return resp(data={'status': 'ok'}, code=200)


@app.route('/add_comment', methods=['POST'])
def add_comment():
    required_fileds = [
        {'name': 'comment_id', 'type': str},
        {'name': 'post_id', 'type': str},
        {'name': 'user_id', 'type': str},
        {'name': 'text', 'type': str}
    ]
    errors = check_request(request=request, fields=required_fileds)
    if errors:
        return resp(code=400, data={'status': 'error', 'errors': errors})

    comment_id = request.json['comment_id']
    post_id = request.json['post_id']
    user_id = request.json['user_id']
    text = request.json['text']
    print("TEXT: {}".format(text))
    text_polarity = sa.get_polarity(text)
    result = db.add_new_comment(
        post_id=post_id,
        user_id=user_id,
        comment_id=comment_id,
        text_polarity=text_polarity
    )
    if result:
        return resp({'status': 'error', 'error': result}, 404)
    return resp(data={'status': 'ok'}, code=200)


@app.route('/predict', methods=['POST'])
def predict():
    required_fileds = [
        {'name': 'text', 'type': str}
    ]
    errors = check_request(request=request, fields=required_fileds)
    if errors:
        return resp(code=400, data={'status': 'error', 'errors': errors})

    text = request.json['text']
    text_themes = tm.get_themes(text)
    predictions = db.predict(text_themes)
    return resp(data={'status': 'ok', 'predictions': predictions}, code=200)


@app.route('/get_users_assesments', methods=['GET'])
def get_average_assesments():
    average_assesments = db.get_users_assesments()
    return resp(
        data={'status': 'ok', 'assesments': average_assesments},
        code=200)


@app.route('/get_average_polaritys', methods=['GET'])
def get_average_polaritys():
    average_polaritys = db.get_users_average_polarityes()
    return resp(
        data={'status': 'ok', 'polaritys': average_polaritys},
        code=200)


@app.route('/status', methods=['GET'])
def get_status():
    currTime = datetime.now()
    response = 'Uptime: {}'.format(currTime - startTime)
    return(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
