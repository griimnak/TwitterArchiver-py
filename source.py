try:
    import twitter
    import requests
except ImportError:
    exit("ImportError, please run pip install -r requirements.txt")

import json
import os
import shutil

from config import conf

try:
    api = twitter.Api(
        # Fill in config fields
        consumer_key=conf["api_key"],
        consumer_secret=conf["api_secret"],
        access_token_key=conf["token_key"],
        access_token_secret=conf["token_secret"],
    )
except:
    exit("Error with config values.")


def target():
    """ :returns: target json"""
    try:
        target = api.GetUser(screen_name=conf["target"])
    except twitter.error.TwitterError as err:
        exit(str(err)+" (please fill out config.py)")
    except:
        exit("Configuration error")
    return target


def get_image(url, path):
    """ makes request to image and saves as file object """
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
            print("[>] get", url, ">>", path)
            f.close()


def get_tweets(api=None, screen_name=None):
    """ get tweet timeline """
    timeline = api.GetUserTimeline(screen_name=screen_name, count=200)
    earliest_tweet = min(timeline, key=lambda x: x.id).id
    print("[+] fetching tweets before:", earliest_tweet)

    while True:
        tweets = api.GetUserTimeline(screen_name=screen_name, max_id=earliest_tweet, count=200)
        new_earliest = min(tweets, key=lambda x: x.id).id

        if not tweets or new_earliest == earliest_tweet:
            break
        else:
            earliest_tweet = new_earliest
            print("[+] fetching tweets before:", earliest_tweet)
            timeline += tweets

    return timeline


def check_dir(dir):
    """ make dir for target if not exists """
    if not os.path.exists(dir):
        print("[+] Creating directory for target..")
        os.makedirs(dir)

# Work
target = target()
work_dir = "data/"+conf["target"]+"/"
summary = f'''[*] Bio url: {target.url}
[*] Register date: {target.created_at}
[*] Tweets: {target.statuses_count}  |  Followers: {target.followers_count}  |  Following: {target.friends_count}  |  Likes: {target.favourites_count} 
[*] Location: {target.location}  |  Name: {target.name}
[*] Latest tweet ({target.status.created_at})  
    "{target.status.text}" ({target.status.retweet_count} Retweets)
    source: {target.status.source}
'''

# Check dir
check_dir(work_dir)

print("[+] Target:", target.screen_name)
print("[+] Downloading profile and banner image..")
# Save media
get_image(target.profile_image_url, work_dir+"profile.jpg")
get_image(target.profile_banner_url, work_dir+"banner.jpg")
print("[*] Done.")

# Generate summary
with open(work_dir+"summary.txt", "w+", encoding="UTF-8") as f:
    print(summary)
    f.write(summary)
    # friends
    count = 0
    print("[+] Fetching friends..")
    friends = api.GetFriends(screen_name=conf["target"])
    f.write("[+] Fetching friends..")
    for u in friends:
        count+=1
        f.write("\n@"+u.screen_name)
    print("[*] Target has", count, "friends")
    print("[*] Summary generated to", work_dir)
    f.close()

# Dump
timeline = get_tweets(api, screen_name=conf["target"])

with open(work_dir+"dump.json", "w+") as f:
    print("[+] Dumping full tweet history to", work_dir, "dump.json")
    for tweet in timeline:
        f.write(json.dumps(tweet._json))
        f.write("\n")
        if(conf["print_timeline"] == True):
            print(f'''[+] Tweet ({tweet.created_at})
     "{tweet.text}"
            
     source: {tweet.source}\n''')
    print("[*] Done.")
    f.close()