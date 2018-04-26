import requests


class SentimentalAnalyzer:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_polarity(self, text):
        dict_to_send = {'raw_text': text}
        res = requests.post(
            'http://' + self.host + ':' + str(self.port) + '/get_polarity',
            json=dict_to_send
        )
        print(res)
        json = res.json()
        return json['polarity']
