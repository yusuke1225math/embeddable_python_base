import tweepy

# TwitterAPIキーを変数に格納
CONSUMER_KEY = "hs1AtD63E6dRPH6kzZqXTp4gm"
CONSUMER_SECRET = "sApWi50ngxHGRoRDe6DlSw98az6d8wvQWs26HGmHbsmj1TgqBu"
ACCESS_TOKEN = "1306062274142986242-vYzPk1qdg8sjW56t0hK7X1ggtsxhCA"
ACCESS_TOKEN_SECRET = "uj6k4EcyuqFQ0ikX8IUiYpfzVkYS1EDlUEYftlqi7q24Q"


def twitter_api_ready():
    try:
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        return tweepy.API(auth, wait_on_rate_limit=True)
    except Exception as e:
        print(e)
        return False
