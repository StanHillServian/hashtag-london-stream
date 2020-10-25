#!/usr/bin/env python3
import apache_beam as beam
import os
import datetime
import csv
import json
from google.cloud import bigquery

table_id = "servian-task:tweets.tweetstream"

def parse_pubsub(line):
    record = json.loads(line)
    yield record

def run():
    projectname = os.getenv('GOOGLE_CLOUD_PROJECT')
    bucketname = "dataflow_temp_london_tweets_poc"
    subscription = 'projects/' + projectname + '/subscriptions/tweets-hashtag-london-topic'
    jobname = 'hashtag-london' + datetime.datetime.now().strftime("%Y%m%d%H%m")
    region = 'europe-west2'

    argv = [
      '--runner=DataflowRunner',
      '--project=' + projectname,
      '--job_name=' + jobname,
      '--region=' + region,
      '--streaming',
      '--staging_location=gs://' + bucketname + '/staging/',
      '--temp_location=gs://' + bucketname + '/temploc/',
      '--save_main_session'
    ]

    p = beam.Pipeline(argv=argv)

    (p
     | 'Read Pubsub' >> beam.io.ReadFromPubSub(subscription=subscription).with_output_types(bytes)
     | 'Process Lines' >> beam.FlatMap(lambda line: parse_pubsub(line))
     | 'Write Row to BigQuery' >> beam.io.WriteToBigQuery(table_id)
     )
    p.run()

if __name__ == '__main__':
    run()