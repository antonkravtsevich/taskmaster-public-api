from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import numpy as np
import os


class DBWorker(object):

    def __init__(self, host, port, database_name):
        try:
            self.mongo_client = MongoClient(host, port, serverSelectionTimeoutMS=1000)
        except ConnectionFailure:
            print("Can't create connection")
            os._exit(1)
        self.db = self.mongo_client[database_name]
        self.clients = self.db['clients']
        self.posts = self.db['posts']
        self.users = self.db['users']
        self.comments = self.db['comments']

    def get_status_ok(self):
        try:
            self.mongo_client.admin.command('ismaster')
            return True
        except ConnectionFailure:
            return False

    # test function
    def clean_database(self):
        self.users.delete_many({})
        self.posts.delete_many({})
        self.comments.delete_many({})
        self.clients.delete_many({})

    def get_clients_collection(self):
        return self.clients

    def get_user_by_id(self, user_id, client_name):
        return self.users.find_one({'user_id': user_id, 'client_name': client_name})

    def get_post_by_id(self, post_id, client_name):
        return self.posts.find_one({'post_id': post_id, 'client_name': client_name})

    def add_new_user(self, user_id, themes, client_name):
        if self.get_user_by_id(user_id, client_name):
            print('USER ALREADY EXIST')
        else: 
            user = {
                'user_id': user_id,
                'themes': themes,
                'client_name': client_name
            }
        self.users.insert_one(user)

    def update_user(self, user_id, themes, client_name):
        user = {
            'user_id': user_id,
            'themes': themes,
            'client_name': client_name
        }
        self.users.update_one(
            {'user_id': user_id},
            {'$set': user},
            upsert=False
        )

    def update_user_prefrences(self, user_id, post_id, polarity, client_name):
        user = self.get_user_by_id(user_id, client_name)
        post = self.get_post_by_id(post_id, client_name)
        post_themes = post['post_themes']
        normalized_themes = []
        for theme in post_themes:
            normalized_themes.append({
                'theme_number': theme['theme_number'],
                'theme_assesment': theme['theme_conformity'] * polarity
            })
        if not user:
            themes = []
            for theme in normalized_themes:
                themes.append({
                    'theme_number': theme['theme_number'],
                    'theme_assesments': [theme['theme_assesment']]
                })
            self.add_new_user(user_id=user_id, themes=themes, client_name=client_name)
        else:
            user_themes = user['themes']
            for n_theme in normalized_themes:
                
                # check if new theme is in old themes list
                themes_coincidented = False
                for u_theme in user_themes:
                    if u_theme['theme_number'] == n_theme['theme_number']:
                        themes_coincidented = True
                        u_theme['theme_assesments'].append(
                            n_theme['theme_assesment']
                        )
                if not themes_coincidented:
                    user_themes.append(
                        {
                            'theme_number': n_theme['theme_number'],
                            'theme_assesments': [n_theme['theme_assesment']]
                        }
                    )
            self.update_user(user_id, user_themes, client_name)

    def add_new_post(self, post_id, post_themes, client_name):
        if self.get_post_by_id(post_id, client_name):
            print('POST ALREADY EXIST')
        else: 
            post = {
                'post_id': post_id,
                'post_themes': post_themes,
                'client_name': client_name
            }
            try:
                self.posts.insert_one(post)
            except Exception as e:
                print(str(e))
                return 'Error in save post to database'
            return None

    def add_new_comment(self, post_id, comment_id, user_id, text_polarity, client_name):
        comment = {
            'post_id': post_id,
            'comment_id': comment_id,
            'user_id': user_id,
            'text_polarity': text_polarity,
            'client_name': client_name
        }
        try:
            self.comments.insert_one(comment)
        except Exception as e:
            print(str(e))
            return 'Error in save comment to database'
        self.update_user_prefrences(
            user_id=user_id,
            post_id=post_id,
            polarity=text_polarity,
            client_name=client_name)
        return None

    def get_users_assesments(self, client_name):
        users = self.users.find({'client_name':client_name})
        assesments = []
        for user in users:
            assesments.append({
                'user_id': user['user_id'],
                'assesments': self.count_user_assesments(user)
            })
        return assesments

    def count_user_assesments(self, user):
        user_themes = user['themes']
        assesments = []
        for theme in user_themes:
            assesments.append({
                'theme_number': theme['theme_number'],
                'theme_assesment': np.mean(theme['theme_assesments'])
            })
        return assesments

    def predict(self, post_themes, client_name):
        print('post_themes: {}'.format(post_themes))
        users = self.get_users_assesments(client_name)
        predictions = []
        for user in users:
            print('user assesments: {}'.format(user['assesments']))
            assesments = []
            for u_theme in user['assesments']:
                u_t_number = u_theme['theme_number']
                u_t_assesment = u_theme['theme_assesment']
                for p_theme in post_themes:
                    p_t_number = p_theme['theme_number']
                    p_t_c = p_theme['theme_conformity']
                    if p_t_number == u_t_number:
                        assesments.append(u_t_assesment * p_t_c)
            if len(assesments) != 0:
                predictions.append({
                    'user_id': user['user_id'],
                    'assesment': np.mean(assesments)
                })
            else:
                predictions.append({
                    'user_id': user['user_id'],
                    'assesment': 0.0
                })
        return predictions

    def get_users_average_polarityes(self, client_name):
        users = self.users.find({'client_name': client_name})
        polaritys = []
        for user in users:
            user_polarity = self.get_user_average_polarity(user['user_id'], client_name=client_name)
            polaritys.append({
                'user_id': user['user_id'], 
                'average_polarity': user_polarity
            })
        return polaritys

    def get_user_average_polarity(self, user_id, client_name):
        comments = self.comments.find({'user_id': user_id, 'client_name': client_name})
        polaritys = []
        for comment in comments:
            polaritys.append(comment['text_polarity'])
        return np.average(polaritys)
