import requests


class ThematicModeller:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_themes(self, text):
        dict_to_send = {'raw_text': text}
        print('dict to send: {}'.format(dict_to_send))
        print('address: {}'.format('http://' + self.host + ':' + str(self.port) + '/get_themes'))
        res = requests.post(
            'http://' + self.host + ':' + str(self.port) + '/get_themes',
            json=dict_to_send
        )
        json = res.json()
        return json['themes']

    def get_theme_words(self, theme_number):
        dict_to_send = {'theme_number': theme_number}
        res = requests.post(
            'http://' + self.host + ':' + str(self.port) + '/get_theme_words',
            json=dict_to_send
        )
        json = res.json()
        return json['words']
