from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import numpy as np
import os


class DBWorker(object):

    def __init__(self, host, port, database_name):
        try:
            self.mongo_client = MongoClient(host, port)
        except ConnectionFailure:
            print("Can't create connection")
            os._exit(1)
        self.db = self.mongo_client[database_name]
        self.clients = self.db['clients']
        self.posts = self.db['posts']
        self.users = self.db['users']
        self.comments = self.db['comments']

    # test function
    def clean_database(self):
        self.users.delete_many({})
        self.posts.delete_many({})
        self.comments.delete_many({})

    def get_clients_collection(self):
        return self.clients

    def get_user_by_id(self, user_id):
        return self.users.find_one({'user_id': user_id})

    def get_post_by_id(self, post_id):
        return self.posts.find_one({'post_id': post_id})

    def add_new_user(self, user_id, themes):
        if self.get_user_by_id(user_id):
            print('USER ALREADY EXIST')
        user = {
            'user_id': user_id,
            'themes': themes
        }
        self.users.insert_one(user)

    def update_user(self, user_id, themes):
        user = {
            'user_id': user_id,
            'themes': themes
        }
        self.users.update_one(
            {'user_id': user_id},
            {'$set': user},
            upsert=False
        )

    def update_user_prefrences(self, user_id, post_id, polarity):
        user = self.get_user_by_id(user_id)
        post = self.get_post_by_id(post_id)
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
            self.add_new_user(user_id=user_id, themes=themes)

        else:
            user_themes = user['themes']
            for n_theme in normalized_themes:
                for u_theme in user_themes:
                    if u_theme['theme_number'] == n_theme['theme_number']:
                        u_theme['theme_assesments'].append(
                            n_theme['theme_assesment']
                        )
            self.update_user(user_id, user_themes)

    def add_new_post(self, post_id, post_themes):
        if self.get_post_by_id(post_id):
            print('POST ALREADY EXIST')
        post = {
            'post_id': post_id,
            'post_themes': post_themes
        }
        try:
            self.posts.insert_one(post)
        except Exception as e:
            print(str(e))
            return 'Error in save post to database'
        return None

    def add_new_comment(self, post_id, comment_id, user_id, text_polarity):
        comment = {
            'post_id': post_id,
            'comment_id': comment_id,
            'user_id': user_id,
            'text_polarity': text_polarity
        }
        try:
            self.comments.insert_one(comment)
        except Exception as e:
            print(str(e))
            return 'Error in save comment to database'
        self.update_user_prefrences(
            user_id=user_id,
            post_id=post_id,
            polarity=text_polarity)
        return None

    def get_users_assesments(self):
        users = self.users.find({})
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

    def predict(self, post_themes):
        users = self.get_users_assesments()
        predictions = []
        for user in users:
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

    def get_users_average_polarityes(self):
        users = self.users.find({})
        polaritys = []
        for user in users:
            user_polarity = self.get_user_average_polarity(user['user_id'])
            polaritys.append({
                'user_id': user['user_id'],
                'average_polarity': user_polarity
            })
        return polaritys

    def get_user_average_polarity(self, user_id):
        comments = self.comments.find({'user_id': user_id})
        polaritys = []
        for comment in comments:
            polaritys.append(comment['text_polarity'])
        return np.average(polaritys)
