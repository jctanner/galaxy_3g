import glob
import json
import os

from logzero import logger

import settings
from indexer import es


def sync_remote_collections(baseurl=None):
    logger.info(f'SYNC {baseurl}')


def get_collection_versions_list(limit=10, offset=0, namespace=None, name=None, version=None, is_highest=None, order_by=None):
    query = {
        "_source": [
            "importer_result.metadata.namespace",
            "importer_result.metadata.name",
            "importer_result.metadata.version",
            "is_highest",
        ],
        "query": {
            "bool": {
                "must": [
                ]
            }
        },
        "size": limit,
        "from": offset,
    }

    if namespace:
        query['query']['bool']['must'].append(
            {"term": {"importer_result.metadata.namespace": namespace}}
        )

    if name:
        query['query']['bool']['must'].append(
            {"term": {"importer_result.metadata.name": name}}
        )

    if is_highest is not None:
        query['query']['bool']['must'].append(
            {"term": {"is_highest": is_highest}}
        )        

    if order_by:
        direction = 'asc'
        if order_by.startswith('-'):
            direction = 'desc'
            order_by = order_by.lstrip('-')
        query['sort'] = {
            f"importer_result.metadata.{order_by}.keyword": { "order": direction }
        }

    response = es.search(index="content_index", body=query)
    versions = []
    for hit in response['hits']['hits']:
        # print(hit)
        transformed = {
            '_id': hit['_id'],
            'namespace': hit['_source']['importer_result']['metadata']['namespace'],
            'name': hit['_source']['importer_result']['metadata']['name'],
            'version': hit['_source']['importer_result']['metadata']['version'],            
        }
        versions.append(transformed)
        
    return response['hits']['total']['value'], versions


def get_collection_version_detail(namespace=None, name=None, version=None):

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"importer_result.metadata.namespace.keyword": namespace}},
                    {"term": {"importer_result.metadata.name.keyword": name}},
                    {"term": {"importer_result.metadata.version.keyword": version}}
                ]
            }
        },
        "size": 1  # Limit the response to only 1 document
    }

    logger.info(json.dumps(query, indent=2))

    response = es.search(index="content_index", body=query)
    logger.info(json.dumps(response['hits']))

    hit = response['hits']['hits'][0]
    transformed = {
        'href': None,
        'namespace': {
            'name': hit['_source']['importer_result']['metadata']['namespace']
        },
        'collection': {
            'name': hit['_source']['importer_result']['metadata']['name'],
        },
        'version': hit['_source']['importer_result']['metadata']['version'],
        'download_url': settings.API_HOSTNAME + \
            f'/api/v3/plugin/ansible/content/published/collections/artifacts/{namespace}-{name}-{version}.tar.gz',
        'artifact': {
            'sha256': None
        },
        'metadata': hit['_source']['importer_result']['metadata'],
    }
    return transformed