import json
import os

import redis
from logzero import logger
from elasticsearch import Elasticsearch
from redis import Redis


# Connect to Redis
redis_conn = Redis(host=os.environ.get('REDIS_HOST'), port=int(os.environ.get('REDIS_PORT')))

# Connect to Elasticsearch
es = Elasticsearch(
    [
        {
            'scheme': 'http',
            'host': os.environ.get('ELASTIC_HOST'),
            'port':int(os.environ.get('ELASTIC_PORT')),
        }
    ],
    verify_certs=False
)


def index_content(metadata):
    # Process the metadata and index it in Elasticsearch
    logger.info('indexing metadata ...')
    es.index(index='content_index', body=metadata)
    logger.info(f"Indexed content: {json.dumps(metadata, indent=2)}")


def listen_for_reindexing():
    pubsub = redis_conn.pubsub()
    pubsub.subscribe('content_reindex')

    for message in pubsub.listen():
        if message['type'] == 'message':
            metadata = eval(message['data'])  # Convert back to dict
            index_content(metadata)


if __name__ == "__main__":
    logger.info("Listening for content reindexing...")
    listen_for_reindexing()
