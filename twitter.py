import tweepy
import utils
import time
import datetime
from datetime import timedelta

import logging
logger = logging.getLogger(__name__)

def get_twitter_api(consumer_key, consumer_secret, access_token, access_secret):
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        api = tweepy.API(auth)
    except Exception:
        logger.exception(f"couldnt create twitter API")
    return api

def get_last_tweets(api, hours, max_tweets):
    
    # init
    tweets = []
    dt = datetime.datetime.now() - timedelta(hours=hours)
    
    # apply 2 hours shift in datetime,
    # cause for some reason tweets creation time is earlier by 2 hours.
    # tweet which was created at 23:00 is shown to be created at 21:00
    dt = dt - timedelta(hours=2)

    curr_tweets = api.home_timeline(count=10)
    while True:
        # update tweets
        tweets += [t for t in curr_tweets if t.created_at > dt]

        # exit condtions
        if not curr_tweets or len(tweets) >= max_tweets:
            break
        elif curr_tweets[-1].created_at <= dt:
            break
        
        # get new tweets
        curr_tweets = api.home_timeline(count=10, max_id=tweets[-1].id-1)
    
    return tweets

def filter_twitter_jobs(api, jobs, hours):
    """ remove jobs which were already posted on twitter at the last given hours """
    
    posted_tweets = get_last_tweets(api, hours=hours, max_tweets=1000)

    # decompose each tweet into its job title and job url
    posted_tweets = [decompose_tweet(t) for t in posted_tweets]

    # remove tweeted jobs
    filterd_jobs = dict()
    for company in jobs:
        filterd_jobs[company] = []
        for job in jobs[company]:
            cond = True
            for (title, url) in posted_tweets:
                if job["title"] == title and job["url"] == url:
                    cond = False
                    break
            if cond:
                filterd_jobs[company].append(job)
    return filterd_jobs
            
def decompose_tweet(tweet):
    """ extract job title and url from given tweet """
    title = tweet.text.split("\n")[0]
    url = tweet.entities["urls"][0]["expanded_url"]
    return title, url

def tweet_jobs(api, jobs):
    """ tweet given jobs """

    logger.info("tweeting new jobs")

    # init
    fails_num = 2  # dont tweet if failed more than given number
    sleep_between_tweets = 12

    for company in jobs:
        for job in jobs[company]:
            tweet = utils.job_to_string(job)
            logger.info(f"tweet {job['url']}")
            try:
                api.update_status(tweet)
            except Exception:
                logger.exception(f"couldnt tweet {job['url']}")
                sleep_between_tweets += sleep_between_tweets
                fails_num -= 1
                logger.info(f"{fails_num} fails left")
            
            # exceeded number of fails
            if fails_num == 0:
                logger.info("too many fails to tweet")
                return 
            
            time.sleep(sleep_between_tweets)
