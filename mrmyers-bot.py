import tweepy
import schedule
import time
from google import genai
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini API
client = genai.Client(api_key=GOOGLE_API_KEY)

# Authenticate with X API v2
twitter_client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Generate tweet using Gemini
def generate_tweet():
    prompt = "act as a cool, chill x content creator focused on personal growth and self-worth. write a single tweet (100 characters or less) in all lowercase, delivering a simple, deep, uplifting message about resilience, boundaries, or self-empowerment. use a reflective, heartfelt, human-like tone with easy-to-understand words. avoid hashtags, emojis, or questions."
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    tweet = response.text.strip()[:100]  # Trim to 100 characters
    return tweet

# Generate reply using Gemini
def generate_reply(post_text):
    prompt = f"act as a cool, chill guy giving an opinion on this x post: '{post_text}'. write a single reply (100 characters or less) in all lowercase, offering a laid-back, thoughtful take. use easy words and avoid hashtags, emojis, or questions."
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    reply = response.text.strip()[:100]  # Trim to 100 characters
    return reply

# Function to post scheduled tweets
def post_scheduled_tweets():
    print(f"Posting scheduled tweets at {time.ctime()}...")
    for i in range(7):
        tweet = generate_tweet()
        try:
            twitter_client.create_tweet(text=tweet)
            print(f"Tweet {i+1} posted: {tweet}")
        except tweepy.TweepyException as e:
            print(f"Error posting tweet {i+1}: {e}")
        time.sleep(2)  # Avoid rate limits

# Function to find and reply to trending tweets (last 5 hours, max 25/day)
def reply_to_trending_tweets():
    print(f"Checking trending tweets at {time.ctime()}...")
    global daily_reply_count
    if 'daily_reply_count' not in globals():
        daily_reply_count = 0

    if daily_reply_count >= 25:
        print("Daily reply limit (25) reached.")
        return

    # Get trends (using WOEID 1 for worldwide)
    trends = twitter_client.get_place_trends(id=1)
    if not trends or not trends[0].trends:
        print("No trends available.")
        return

    # Get current time and 5 hours ago
    current_time = datetime.utcnow()
    five_hours_ago = current_time - timedelta(hours=5)

    # Limit replies to 2-3 per check to reach ~25/day over 12 checks
    max_replies_per_check = min(3, 25 - daily_reply_count)
    if max_replies_per_check <= 0:
        return

    for trend in trends[0].trends[:3]:  # Top 3 trends
        query = f"{trend.name} -filter:retweets -filter:replies"
        tweets = twitter_client.search_recent_tweets(query=query, max_results=10)
        if tweets.data:
            valid_tweets = [t for t in tweets.data if datetime.strptime(t.created_at, "%Y-%m-%dT%H:%M:%S.%fZ") > five_hours_ago]
            for tweet in valid_tweets[:max_replies_per_check]:  # Limit per trend
                reply = generate_reply(tweet.text)
                try:
                    twitter_client.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)
                    print(f"Replied to {tweet.id} with: {reply}")
                    daily_reply_count += 1
                    if daily_reply_count >= 25:
                        print("Daily reply limit reached.")
                        return
                except tweepy.TweepyException as e:
                    print(f"Error replying to {tweet.id}: {e}")
                time.sleep(1)  # Avoid rate limits

# Schedule tasks
schedule.every().day.at("00:00").do(post_scheduled_tweets)  # Midnight
schedule.every().day.at("02:00").do(post_scheduled_tweets)  # 2 AM
schedule.every().day.at("08:00").do(post_scheduled_tweets)  # 8 AM
schedule.every().day.at("12:00").do(post_scheduled_tweets)  # Noon
schedule.every().day.at("15:00").do(post_scheduled_tweets)  # 3 PM
schedule.every().day.at("18:00").do(post_scheduled_tweets)  # 6 PM
schedule.every().day.at("21:00").do(post_scheduled_tweets)  # 9 PM
schedule.every(5).hours.do(reply_to_trending_tweets)  # Every 5 hours

# Test
# Run the scheduler
if __name__ == "__main__":
    print("Bot started. Running scheduled tasks...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute