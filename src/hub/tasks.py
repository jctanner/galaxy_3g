import json
import os
from logzero import logger
from redis import Redis
from galaxy_importer.collection import import_collection as process_collection
from ansible.utils.version import SemanticVersion

import settings
from indexer import es
from collection_utils import get_collection_versions_list
from pulp_client import PulpCoreClient


def process_collection_upload(filename):

    print(f'PROCESS COLLECTION {filename}')

    # run galaxy-importer on the file
    with open(filename, 'rb') as fh:
        importer_result = process_collection(
            file=fh, filename=filename, logger=logger
        )

    logger.info(json.dumps(importer_result, indent=2))

    # store the importer data
    ifn = filename + '.gi.json'
    with open(ifn, 'w') as f:
        f.write(json.dumps(importer_result, indent=2))

    # init the pulpcore client
    pc = PulpCoreClient()

    # upload the file to pulp
    pulp_data = pc.upload_file(filename, repository_name=settings.DEFAULT_REPOSITORY_NAME)
    logger.info(json.dumps(pulp_data, indent=2))

    # compute the current highest version ...
    namespace = importer_result['metadata']['namespace']
    name = importer_result['metadata']['name']
    version = importer_result['metadata']['version']
    is_highest = False

    total_count, cvs = get_collection_versions_list(
        namespace=namespace,
        name=name,
        limit=1000,
    )

    vmap = {}
    for cv in cvs:
        vmap[cv['version']] = cv['_id']

    logger.info(vmap)
    if version in vmap:
        raise Exception(f'{namespace}.{name}=={version} has already been uploaded')
        # pass

    vlist = [(SemanticVersion(x), x) for x in list(vmap.keys())]
    vlist = sorted(vlist, reverse=True, key=lambda x: x[0])
    logger.info(vlist)
    if vlist:
        current_highest = vlist[0]
    else:
        current_highest = None

    if current_highest is None:
        is_highest = True
    else:
        index = "content_index"
        if SemanticVersion(version) > current_highest[0]:
            is_highest = True
            # set is_highest=False on all the other versions ...
            for vname, vid in vmap.items():
                es.update(
                    index=index,
                    id=vid,
                    body={
                        "doc": {
                            "is_highest": False
                        }
                    }
                )

    logger.info(vmap)
    if version in vmap:
        # raise Exception(f'{namespace}.{name}=={version} has already been uploaded')
        pass

    metadata = {
        'importer_result': importer_result,
        'pulp': pulp_data,
        'is_highest': is_highest
    }

    # store the importer data AND the pulp_data in the database ...
    redis_conn = Redis(host=os.environ.get('REDIS_HOST'), port=int(os.environ.get('REDIS_PORT')))
    redis_conn.publish('content_reindex', str(metadata))

    return {}
