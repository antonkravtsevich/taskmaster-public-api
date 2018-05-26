import unittest
from src.tm import ThematicModeller
from src.sa import SentimentalAnalyzer
from src.db_worker import DBWorker


class TestAPI(unittest.TestCase):

    def test_tm_service_get_themes(self):
        print('test_tm_service_get_themes')
        tm = ThematicModeller(host='188.166.115.138', port=30962)
        text = 'A video game is an electronic game that involves '\
            'interaction with a user interface to generate visual '\
            'feedback on a video device such as a TV screen or computer '\
            'monitor. The word video in video game traditionally '\
            'referred to a raster display device, but as of the 2000s, '\
            'it implies any type of display device that can produce '\
            'two- or three-dimensional images. Some theorists categorize '\
            'video games as an art form, but this designation is '\
            'controversial.'
        themes_info = tm.get_themes(text)
        themes = []
        for pair in themes_info:
            themes.append(pair['theme_number'])
        self.assertIn(31, themes)
        self.assertIn(36, themes)
        self.assertIn(85, themes)

    def test_tm_service_get_theme_words(self):
        print('test_tm_service_get_theme_words')
        tm = ThematicModeller(host='188.166.115.138', port=30962)
        words_info = tm.get_theme_words(36)
        words = []
        for pair in words_info:
            words.append(pair['word'])
        self.assertIn('game', words)
        self.assertIn('gameplay', words)
        self.assertIn('player', words)
        self.assertIn('video', words)

    def test_sa_service_get_polarity_positive(self):
        print('test_sa_service_get_polarity_positive')
        sa = SentimentalAnalyzer(host='188.166.115.138', port=31206)
        text = 'that is so cool awesome good wow'
        result = sa.get_polarity(text)
        self.assertGreater(result, 0)

    def test_sa_service_get_polarity_negative(self):
        print('test_sa_service_get_polarity_negative')
        sa = SentimentalAnalyzer(host='188.166.115.138', port=31206)
        text = 'ugly bad worse awfull terrible'
        result = sa.get_polarity(text)
        self.assertLess(result, 0)

    def test_db_worker_update_user_prefrence(self):
        print('test_db_worker_update_user_prefrence')
        db = DBWorker(host='188.166.115.138', port=31178, database_name='tm_test')
        db.clean_database()
        themes1 = [
            {
                'theme_number': 1,
                'theme_conformity': 0.8
            },
            {
                'theme_number': 2,
                'theme_conformity': 0.4
            }
        ]
        themes2 = [
            {
                'theme_number': 2,
                'theme_conformity': 0.8
            }
        ]
        db.add_new_post(post_id=1, post_themes=themes1, client_name='test_client')
        db.add_new_post(post_id=2, post_themes=themes2, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=1, polarity=0.5, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=2, polarity=0.5, client_name='test_client')
        user = db.get_user_by_id(user_id=1, client_name='test_client')
        del(user['_id'])
        test_user = {
            'user_id': 1,
            'themes': [
                {
                    'theme_number': 1,
                    'theme_assesments': [0.4]
                },
                {
                    'theme_number': 2,
                    'theme_assesments': [0.2, 0.4]
                }
            ]
        }
        db.clean_database()
        self.assertEqual(user, test_user)

    def test_db_worker_count_user_assesments(self):
        print('test_db_worker_count_user_assesments')
        db = DBWorker(host='188.166.115.138', port=31178, database_name='tm_test')
        db.clean_database()
        themes3 = [
            {
                'theme_number': 1,
                'theme_conformity': 0.8
            },
            {
                'theme_number': 2,
                'theme_conformity': 0.4
            }
        ]
        themes4 = [
            {
                'theme_number': 2,
                'theme_conformity': 0.8
            }
        ]
        db.add_new_post(post_id=1, post_themes=themes3, client_name='test_client')
        db.add_new_post(post_id=2, post_themes=themes4, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=1, polarity=0.5, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=2, polarity=0.5, client_name='test_client')
        user = db.get_user_by_id(1, client_name='test_client')
        assesment = db.count_user_assesments(user=user)
        test_assesment = [
            {
                'theme_number': 1,
                'theme_assesment': 0.4
            },
            {
                'theme_number': 2,
                'theme_assesment': 0.30000000000000004
            }
        ]
        db.clean_database()
        self.assertEqual(assesment, test_assesment)

    def test_db_worker_get_users_assesments(self):
        print('test_db_worker_get_users_assesments')
        db = DBWorker(host='188.166.115.138', port=31178, database_name='tm_test')
        db.clean_database()
        themes1 = [
            {
                'theme_number': 1,
                'theme_conformity': 0.8
            },
            {
                'theme_number': 2,
                'theme_conformity': 0.4
            }
        ]
        themes2 = [
            {
                'theme_number': 2,
                'theme_conformity': 0.8
            }
        ]
        db.add_new_post(post_id=1, post_themes=themes1, client_name='test_client')
        db.add_new_post(post_id=2, post_themes=themes2, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=1, polarity=0.5, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=2, polarity=0.5, client_name='test_client')
        db.update_user_prefrences(user_id=2, post_id=2, polarity=1, client_name='test_client')
        assesments = db.get_users_assesments(client_name='test_client')
        test_assesments = [
            {
                'user_id': 1,
                'assesments': [
                    {
                        'theme_number': 1,
                        'theme_assesment': 0.4
                    },
                    {
                        'theme_number': 2,
                        'theme_assesment': 0.30000000000000004
                    }
                ]
            },
            {
                'user_id': 2,
                'assesments': [
                    {
                        'theme_number': 2,
                        'theme_assesment': 0.8
                    }
                ]
            }

        ]
        db.clean_database()
        self.assertEqual(assesments, test_assesments)

    def test_db_worker_predictions(self):
        print('test_db_worker_predictions')
        db = DBWorker(host='188.166.115.138', port=31178, database_name='tm_test')
        db.clean_database()
        themes1 = [
            {
                'theme_number': 1,
                'theme_conformity': 0.8
            },
            {
                'theme_number': 2,
                'theme_conformity': 0.4
            }
        ]
        themes2 = [
            {
                'theme_number': 2,
                'theme_conformity': 0.8
            }
        ]
        db.add_new_post(post_id=1, post_themes=themes1, client_name='test_client')
        db.add_new_post(post_id=2, post_themes=themes2, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=1, polarity=0.5, client_name='test_client')
        db.update_user_prefrences(user_id=1, post_id=2, polarity=0.5, client_name='test_client')
        db.update_user_prefrences(user_id=2, post_id=2, polarity=1, client_name='test_client')
        themes3 = [
            {
                'theme_number': 1,
                'theme_conformity': 1.0
            }
        ]
        predictions = db.predict(themes3)
        test_predictions = [
            {
                'user_id': 1,
                'assesment': 0.4
            },
            {
                'user_id': 2,
                'assesment': 0.0
            }

        ]
        db.clean_database()
        self.assertEqual(predictions, test_predictions)

    def test_db_worker_get_average_polarity(self):
        print('test_db_worker_get_average_polarity')
        db = DBWorker(host='188.166.115.138', port=31178, database_name='tm_test')
        db.clean_database()
        db.add_new_post(
            post_id=1,
            post_themes=[
                {
                    'theme_number': 1,
                    'theme_conformity': 1.0
                }
            ], client_name='test_client'
        )
        db.add_new_post(
            post_id=2,
            post_themes=[
                {
                    'theme_number': 2,
                    'theme_conformity': 1.0
                }
            ], client_name='test_client'
        )
        db.add_new_comment(
            post_id=1,
            user_id=1,
            comment_id=1,
            text_polarity=1.0, 
            client_name='test_client')
        db.add_new_comment(
            post_id=2,
            user_id=1,
            comment_id=2,
            text_polarity=1.0,
             client_name='test_client')
        avg_polarity = db.get_user_average_polarity(user_id=1, client_name='test_client')
        db.clean_database()
        self.assertEqual(avg_polarity, 1.0)

    def test_db_worker_get_users_average_polaritys(self):
        db = DBWorker(host='188.166.115.138', port=31178, database_name='tm_test')
        db.clean_database()
        db.add_new_post(
            post_id=1,
            post_themes=[
                {
                    'theme_number': 1,
                    'theme_conformity': 1.0
                }
            ], client_name='test_client'
        )
        db.add_new_post(
            post_id=2,
            post_themes=[
                {
                    'theme_number': 2,
                    'theme_conformity': 1.0
                }
            ], client_name='test_client'
        )
        db.add_new_comment(
            post_id=1,
            user_id=1,
            comment_id=1,
            text_polarity=1.0,
            client_name='test_client')
        db.add_new_comment(
            post_id=2,
            user_id=1,
            comment_id=2,
            text_polarity=1.0,
            client_name='test_client')
        polaritys = db.get_users_average_polarityes(client_name='test_client')
        test_polaritys = [
            {
                'user_id': 1,
                'average_polarity': 1.0
            }
        ]
        db.clean_database()
        self.assertEqual(polaritys, test_polaritys)

if __name__ == '__main__':
    unittest.main()
