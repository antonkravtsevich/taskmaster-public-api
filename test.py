import unittest
import src.app as app

class TestAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestAPI, self).__init__(*args, **kwargs)
        self.collection = app.get_collection()


    def test_add_to_database(self):
        theme = 'theme'
        text = 'text'
        timestamp = '1522747384843'
        polarity = 0.0
        app.add_to_database(collection=self.collection, timestamp=timestamp, theme=theme, text=text, polarity=polarity)
        result = app.get_posts_from_database(collection=self.collection, theme=theme)
        self.assertEqual(len(result), 1)
        self.assertEqual(theme, result[0]['theme'])
        self.assertEqual(text, result[0]['text'])
        self.assertEqual(polarity, result[0]['polarity'])


if __name__ == '__main__':
    unittest.main()