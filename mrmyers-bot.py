import tweepy
import schedule
import time
from google import genai
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from keep_alive import keep_alive
from datetime import datetime

print("Server time is:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Keep Replit app alive
keep_alive()

# Load environment variables
load_dotenv()

# Environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)

# Tweepy API v2 (for posting & searching)
twitter_client = tweepy.Client(consumer_key=API_KEY,
                               consumer_secret=API_SECRET,
                               access_token=ACCESS_TOKEN,
                               access_token_secret=ACCESS_TOKEN_SECRET)

# Tweepy API v1.1 (for trends)
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN,
                                ACCESS_TOKEN_SECRET)
twitter_api_v1 = tweepy.API(auth)


# Generate tweet using Gemini
def generate_tweet():
    prompt = "act as a cool, chill x content creator focused on personal growth and self-worth. write a single tweet (100 characters or less) in all lowercase, delivering a simple, deep, uplifting message about resilience, boundaries, or self-empowerment. use a reflective, heartfelt, human-like tone with easy-to-understand words. avoid hashtags, emojis, or questions."
    response = client.models.generate_content(model="gemini-2.5-flash",
                                              contents=prompt)
    return response.text.strip()[:100]


# Generate reply using Gemini
def generate_reply(post_text):
    prompt = f"act as a cool, chill guy giving an opinion on this x post: '{post_text}'. write a single reply (100 characters or less) in all lowercase, offering a laid-back, thoughtful take. use easy words and avoid hashtags, emojis, or questions."
    response = client.models.generate_content(model="gemini-2.5-flash",
                                              contents=prompt)
    return response.text.strip()[:100]


# Tweet 1 times per schedule
def post_scheduled_tweets():
    print(f"Posting scheduled tweets at {time.ctime()}...")
    for i in range(1):
        tweet = generate_tweet()
        try:
            twitter_client.create_tweet(text=tweet)
            print(f"Tweet {i+1} posted: {tweet}")
        except tweepy.TweepyException as e:
            print(f"Error posting tweet {i+1}: {e}")
        time.sleep(2)


# Reply to trending tweets
daily_reply_count = 0


def reply_to_trending_tweets():
    global daily_reply_count
    print(f"Checking trending tweets at {time.ctime()}...")

    if daily_reply_count >= 25:
        print("Daily reply limit (25) reached.")
        return

    try:
        trends_result = twitter_api_v1.get_place_trends(
            id=1)  # WOEID 1 = Worldwide
    except Exception as e:
        print(f"Error getting trends: {e}")
        return

    trends = trends_result[0]['trends'][:3]
    current_time = datetime.utcnow()
    five_hours_ago = current_time - timedelta(hours=5)

    replies_sent = 0
    for trend in trends:
        query = f"{trend['name']} -is:retweet -is:reply lang:en"
        try:
            search_results = twitter_client.search_recent_tweets(
                query=query, max_results=10, tweet_fields=["created_at"])
        except Exception as e:
            print(f"Search error: {e}")
            continue

        if search_results.data:
            for tweet in search_results.data:
                if tweet.created_at > five_hours_ago and daily_reply_count < 25:
                    reply = generate_reply(tweet.text)
                    try:
                        twitter_client.create_tweet(
                            text=reply, in_reply_to_tweet_id=tweet.id)
                        print(f"Replied to {tweet.id} with: {reply}")
                        daily_reply_count += 1
                        replies_sent += 1
                        time.sleep(1)
                    except tweepy.TweepyException as e:
                        print(f"Reply error: {e}")
        if replies_sent >= 3:
            break


# Scheduling
schedule.every().day.at("00:00").do(post_scheduled_tweets)
schedule.every().day.at("02:00").do(post_scheduled_tweets)
schedule.every().day.at("08:00").do(post_scheduled_tweets)
schedule.every().day.at("12:00").do(post_scheduled_tweets)
schedule.every().day.at("15:00").do(post_scheduled_tweets)
schedule.every().day.at("16:43").do(post_scheduled_tweets)
schedule.every().day.at("18:00").do(post_scheduled_tweets)
schedule.every().day.at("21:00").do(post_scheduled_tweets)
schedule.every(5).hours.do(reply_to_trending_tweets)

# Bot Loop
if __name__ == "__main__":
    print("Bot started. Running scheduled tasks...")
    while True:
        schedule.run_pending()
        time.sleep(60)
