import json
import html
from lib import cleaing_txt

def cleaning_tweet(tweets_js_path: str = 'tweets.js', save_path: str = 'cleaned_tweets.txt') -> None:
    with open(tweets_js_path, 'r') as f:
        raw_txt = f.read()

    raw_txt = raw_txt.replace('window.YTD.tweets.part0 = ', '')
    json_data = json.loads(raw_txt)

    tweets = []
    for tweet in json_data:
        txt = tweet['tweet']['full_text']

        # リツイートはスキップ
        if txt.startswith('RT @'):
            continue
        # AtCoderの成績を含むツイートはスキップ
        if "shinnshinnさんの" in txt:
            continue
        # AtCoderの提出を含むツイートはスキップ
        if '提出 #' in txt:
            continue

        txt = html.unescape(txt)
        txt = cleaing_txt(txt)

        if len(txt) == 0:
            continue

        tweets.append(txt)

    with open(save_path, 'w') as f:
        f.write('\n'.join(tweets))

cleaning_tweet()
