import markovify
import MeCab

def create_model():
    tagger = MeCab.Tagger('-Owakati')

    with open('clean_bluesky_posts.txt') as f:
        text = f.readlines()
    with open('cleaned_tweets.txt') as f:
        text.extend(f.readlines())

    wakati_text = ""
    for i in range(len(text)):
        wakati_text += tagger.parse(text[i])

    model = markovify.NewlineText(wakati_text)
    model = model.compile()

    model_json = model.to_json()
    with open('model.json', 'w') as f:
        f.write(model_json)

if __name__ == '__main__':
    create_model()
