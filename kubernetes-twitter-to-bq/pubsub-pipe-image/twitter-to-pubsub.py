#!/usr/bin/env python

"""This script uses the Twitter Streaming API, via the tweepy library,
to pull in tweets and publish them to a PubSub topic.
"""

import base64
import datetime
import os
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import json 
import datetime
import hashlib
from dateutil.parser import parse

import utils

# Get your twitter credentials from the environment variables.
# These are set in the 'twitter-stream.json' manifest file.
consumer_key = os.environ['CONSUMERKEY']
consumer_secret = os.environ['CONSUMERSECRET']
access_token = os.environ['ACCESSTOKEN']
access_token_secret = os.environ['ACCESSTOKENSEC']

PUBSUB_TOPIC = os.environ['PUBSUB_TOPIC']
NUM_RETRIES = 3




def publish(client, pubsub_topic, data_lines):
    messages = []
    """Publish to the given pubsub topic."""
    for line in data_lines:
        data = json.loads(line)
        try:
            #HASH TWITTER HANDLE
            user = data["user"]
            hash_obj = hashlib.sha1(user["screen_name"].encode('utf-8'))
            pbHash = hash_obj.hexdigest()
            hashed_handle = "@[{}]".format(pbHash)
            
            #GET DATE IN EXPECTED FORMAT
            date=str(parse(data["created_at"]))
            datetime=date.split('+', 1)[0]

            clean_data=json.dumps({
                "tweet": data["text"],
                "user_handle_hashed": hashed_handle,
                "posted_at": datetime
            }).encode("utf-8")
            pub = base64.urlsafe_b64encode(clean_data)
            messages.append({'data': pub})
     
        except Exception as e:
            print(e)
            raise
    body = {'messages': messages}
    resp = client.projects().topics().publish(
            topic=pubsub_topic, body=body).execute(num_retries=NUM_RETRIES)
    return resp


class StdOutListener(StreamListener):
    """A listener handles tweets that are received from the stream.
    This listener dumps the tweets into a PubSub topic
    """

    count = 0
    twstring = ''
    tweets = []
    batch_size = 5
    total_tweets = 10000000
    client = utils.create_pubsub_client(utils.get_credentials())

    def write_to_pubsub(self, tw):
        publish(self.client, PUBSUB_TOPIC, tw)

    def on_data(self, data):
        """What to do when tweet data is received."""
        self.tweets.append(data)
        if len(self.tweets) >= self.batch_size:
            self.write_to_pubsub(self.tweets)
            self.tweets = []
        self.count += 1
        # if we've grabbed more than total_tweets tweets, exit the script.
        # If this script is being run in the context of a kubernetes
        # replicationController, the pod will be restarted fresh when
        # that happens.
        if self.count > self.total_tweets:
            return False
        if (self.count % 1000) == 0:
            print 'count is: %s at %s' % (self.count, datetime.datetime.now())
        return True

    def on_error(self, status):
        print status


if __name__ == '__main__':
    print '....'
    listener = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    print 'stream mode is: %s' % os.environ['TWSTREAMMODE']

    stream = Stream(auth, listener)
    # set up the streaming depending upon whether our mode is 'filter', which
    # will stream the #london hashtag. If it is not, it will sample random 
    # This environment var is set in the 'twitter-stream.yaml' file.
    if os.environ['TWSTREAMMODE'] == 'filter':
        stream.filter(track=['#london'])
    else:
        print 'stream mode needs to be filter!'
                
