import base64
import datetime
import os

from flask import Flask, Response, jsonify, request, redirect, stream_with_context
from redis import Redis
from rq import Queue, Worker
from rq.job import Job
import time

import settings
from pulp_client import PulpCoreClient
import tasks
import collection_utils
from indexer import es


app = Flask(__name__)
redis_conn = Redis(host=os.environ.get('REDIS_HOST'), port=int(os.environ.get('REDIS_PORT')))
queue = Queue('default', connection=redis_conn)

DS = {
    'repositories': [],
    'collections': [],
    'roles': [],
}


@app.before_request
def initialize():

    # return

    # mimics the old before_first_request behavior ...
    app.before_request_funcs[None].remove(initialize)

    # init the pulpcore client
    pc = PulpCoreClient()

    # make the default repo
    repo = pc.create_repository(settings.DEFAULT_REPOSITORY_NAME)

    # make the default distro
    distro = pc.create_distribution(repo, settings.DEFAULT_DISTRIBUTION_NAME)

    # make the default index
    es.indices.create(index="content_index")


@app.route('/')
def root():
    return redirect('/api/')


@app.route('/api/')
def api_root():
    return jsonify({
        'available_versions': {
            'v3': '/api/v3/',
            'v4': '/api/v4/',
        }
    })

################################
# v4
################################

@app.route('/api/v4/')
def api_v4_root():
    return jsonify({
        'collections': '/api/v4/collections/',
        'roles': '/api/v4/roles/',
    })


@app.route('/api/v4/environment/')
def environment():
    return jsonify(dict(os.environ))


@app.route('/api/v4/repositories/')
def repositories():
    return jsonify(DS['repositories'])


################################
# _ui/v1
################################

@app.route('/login/github/')
def login_github():
    return jsonify({})


#@app.route('/login/github/')
#def login_github():
#    return jsonify({})


@app.route('/api/_ui/v1/collection-versions/')
def ui_v1_collection_versions():
    versions = collection_utils.get_collection_versions_list()
    return jsonify({
        'data': versions
    })


@app.route('/api/_ui/v1/me/')
def ui_v1_me():
    return jsonify({
        "id": None,
        "username": "",
        "groups": [],
        "is_superuser": False,
        "is_anonymous": True,
        "auth_provider": [
            "django"
        ],
    })

@app.route('/api/_ui/v1/settings/')
def ui_v1_settings():
    return jsonify({
      "GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_ACCESS": True,
      "GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_DOWNLOAD": True,
      "GALAXY_FEATURE_FLAGS": {
        "legacy_roles": True,
        "external_authentication": True,
        "display_repositories": False,
        "ai_deny_index": True,
        "execution_environments": False,
        "collection_signing": False,
        "require_upload_signatures": False,
        "signatures_enabled": False,
        "can_upload_signatures": False,
        "can_create_signatures": False,
        "collection_auto_sign": False,
        "display_signatures": False,
        "container_signing": False,
        "_messages": []
      },
      "GALAXY_TOKEN_EXPIRATION": None,
      "GALAXY_REQUIRE_CONTENT_APPROVAL": False,
      "GALAXY_COLLECTION_SIGNING_SERVICE": None,
      "GALAXY_AUTO_SIGN_COLLECTIONS": False,
      "GALAXY_SIGNATURE_UPLOAD_ENABLED": False,
      "GALAXY_REQUIRE_SIGNATURE_FOR_APPROVAL": False,
      "GALAXY_MINIMUM_PASSWORD_LENGTH": None,
      "GALAXY_AUTH_LDAP_ENABLED": None,
      "GALAXY_CONTAINER_SIGNING_SERVICE": None,
      "GALAXY_LDAP_MIRROR_ONLY_EXISTING_GROUPS": False,
      "GALAXY_LDAP_DISABLE_REFERRALS": None,
      "KEYCLOAK_URL": None
    })


@app.route('/api/_ui/v1/feature-flags/')
def ui_v1_feature_flags():
    return jsonify({
        "legacy_roles": True,
        "external_authentication": True,
        "display_repositories": False,
        "ai_deny_index": True,
        "execution_environments": False,
        "collection_signing": False,
        "require_upload_signatures": False,
        "signatures_enabled": False,
        "can_upload_signatures": False,
        "can_create_signatures": False,
        "collection_auto_sign": False,
        "display_signatures": False,
        "container_signing": False,
        "_messages": []
    })


################################
# v3
################################

@app.route('/api/v3/auth/token/', methods=['POST'])
def v3_auth_token():
    return jsonify({
    })


@app.route('/api/pulp/api/v3/distributions/ansible/ansible/')
def v3_pulp_distributions_ansible_ansible():
    """
        {
            "pulp_href": "/api/pulp/api/v3/distributions/ansible/ansible/39c70700-124d-40c1-b412-b8712ade7712/",
            "pulp_created": "2023-05-08T20:13:25.950910Z",
            "base_path": "validated",
            "content_guard": "/api/pulp/api/v3/contentguards/core/content_redirect/ea4105ed-aba8-4c35-876c-d34a4b36d37e/",
            "name": "validated",
            "repository": "/api/pulp/api/v3/repositories/ansible/ansible/b3ea104e-b892-4c68-a26f-c9d51a8efadf/",
            "repository_version": null,
            "client_url": "https://galaxy.ansible.com/pulp_ansible/galaxy/validated/",
            "pulp_labels": {}
        },
    """
    return jsonify({
        'results': [
            {
                'pulp_href': None,
                'pulp_created': None,
                'base_path': 'published',
                'name': 'published',
                'repository': None,
                'repository_version': None,
                'client_url': None,
                'pulp_labels': {}
            }
        ]
    })


@app.route('/api/pulp/api/v3/repositories/ansible/ansible/')
def v3_pulp_repositories_ansible_ansible():
    """
        {
            "pulp_href": "/api/pulp/api/v3/repositories/ansible/ansible/b3ea104e-b892-4c68-a26f-c9d51a8efadf/",
            "pulp_created": "2023-05-08T20:13:25.940562Z",
            "versions_href": "/api/pulp/api/v3/repositories/ansible/ansible/b3ea104e-b892-4c68-a26f-c9d51a8efadf/versions/",
            "pulp_labels": {},
            "latest_version_href": "/api/pulp/api/v3/repositories/ansible/ansible/b3ea104e-b892-4c68-a26f-c9d51a8efadf/versions/0/",
            "name": "validated",
            "description": "Validated collections",
            "retain_repo_versions": null,
            "remote": null,
            "last_synced_metadata_time": null,
            "gpgkey": null,
            "last_sync_task": null,
            "private": false
        },
    """

    return jsonify({
        'results': [
            {
                'pulp_href': None,
                'pulp_created': None,
                'versions_href': None,
                'pulp_labels': {},
                'latest_version_href': None,
                'name': 'published',
                'description': None,
                'retain_repo_versions': None,
                'remote': None,
                'last_synced_metadata_time': None,
                'gpgkey': None,
                'last_sync_task': None,
                'private': False,
            }
        ]
    })


@app.route('/api/v3/plugin/ansible/content/published/collections/index/<namespace>/<name>/')
def v3_pulp_content_collections_index_namespace_name(namespace, name):
    return jsonify({
        'namespace': namespace,
        'name': name,
        'deprecated': False,
        'versions_url': None,
        'highest_version': {
        },
        'created_at': None,
        'updated_at': None,
        'download_count': None,
    })


@app.route('/api/pulp/api/v3/content/ansible/collection_versions/')
def v3_pulp_content_collection_versions():
    # ?namespace=ansible&name=netcommon&version=1.1.3-dev6&offset=0&limit=10
    """
    count:
    next:
    previous:
    results:
        - pulp_created
          dependencies
          docs_blob
          name
          namespace
    """

    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    namespace = request.args.get('namespace', default=None)
    name = request.args.get('name', default=None)
    version = request.args.get('version', default=None)

    total_versions, versions = collection_utils.get_collection_versions_list(
        limit=limit,
        offset=offset,
        namespace=namespace,
        name=name,
        version=version,
    )

    transformed = []
    for cv in versions:
        transformed.append({
            'namespace': cv['namespace'],
            'name': cv['name'],
            'version': cv['version'],
        })

    return jsonify({
        'count': total_versions,
        'next': None,
        'previous': None,
        'results': transformed,
    })


@app.route('/api/v3/search/collection-versions/')
@app.route('/api/v3/plugin/ansible/search/collection-versions/')
def v3_collection_search():

    # "/api/v3/plugin/ansible/search/collection-versions/?limit=10&offset=10"

    limit = request.args.get('limit', default=10, type=int)
    offset = request.args.get('offset', default=0, type=int)
    namespace = request.args.get('namespace', default=None)
    name = request.args.get('name', default=None)
    version = request.args.get('version', default=None)
    is_highest = request.args.get('is_highest', default=None, type=bool)
    order_by = request.args.get('order_by', default=None)

    total_versions, versions = collection_utils.get_collection_versions_list(
        limit=limit,
        offset=offset,
        namespace=namespace,
        name=name,
        version=version,
        is_highest=is_highest,
        order_by=order_by,
    )

    transformed = []
    for version in versions:
        transformed.append({
            'repository': {
                'name': 'published',
            },
            'collection_version': {
                'namespace': version['namespace'],
                'name': version['name'],
                'version': version['version'],
                'contents': [],
                'dependencies': {},
                'description': None,
                'tags': [],
            },
            'namespace_metadata': {
                'name': version['namespace'],
                'company': None,
            },
            'is_highest': False,
            'is_deprecated': False,
            'is_signed': False,
        })

    return jsonify({
        'meta': {
            'count': total_versions,
        },
        'links': {
            'first': None,
            'previous': None,
            'next': None,
            'last': None,
        },
        'data': transformed
    })


@app.route('/api/v3/artifacts/collections/', methods=['POST'])
def v3_artifacts_collections():

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    print(f'FILES: {request.files}')


    file = request.files['file']

    os.makedirs(settings.COLLECTION_UPLOAD_FOLDER, exist_ok=True)

    file_path = os.path.join(settings.COLLECTION_UPLOAD_FOLDER, file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # file.save(file_path)

    '''
    try:
        # Save the uploaded file in binary mode
        with open(file_path, 'wb') as f:
            f.write(file.read())
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    '''

    try:
        # Read the file content as Base64-encoded string
        base64_data = file.read()

        # Decode the Base64 data to binary
        binary_data = base64.b64decode(base64_data)

        # Save the binary data to a file
        with open(file_path, 'wb') as f:
            f.write(binary_data)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500

    job = queue.enqueue('tasks.process_collection_upload', file_path)

    return jsonify({
        'task': job.get_id()
    })


@app.route('/api/v3/imports/collections/<taskid>/', methods=['GET'])
def v3_artifacts_collections_task(taskid):
    try:
        # Fetch the job from RQ using the task ID
        job = Job.fetch(taskid, connection=redis_conn)
    except Exception as e:
        return jsonify({'error': 'Task not found'}), 404

    # Determine the job state
    if job.is_finished:
        state = 'completed'
        finished_at = job.ended_at.isoformat() if job.ended_at else datetime.datetime.now().isoformat()
        result = job.result
    elif job.is_failed:
        state = 'failed'
        finished_at = job.ended_at.isoformat() if job.ended_at else datetime.datetime.now().isoformat()
        result = str(job.exc_info)  # Include error info
    else:
        state = 'in progress'
        finished_at = None
        result = None

    return jsonify({
        'state': state,
        'finished_at': finished_at,
        'result': result,
    })


@app.route('/api/v3/collections/<namespace>/<name>/', methods=['GET'])
def v3_collections(namespace, name):
    return jsonify({
        'href': f"/api/v3/plugin/ansible/content/published/collections/index/{namespace}/{name}/",
        'namespace': namespace,
        'name': name,
        'highest_version': {},
        'versions_url': f"/api/v3/plugin/ansible/content/published/collections/index/{namespace}/{name}/versions/",
    })


@app.route('/api/v3/collections/<namespace>/<name>/versions/', methods=['GET'])
@app.route('/api/v3/plugin/ansible/content/published/collections/index/<namespace>/<name>/versions/', methods=['GET'])
def v3_collections_versions(namespace, name):
    total_versions, versions = collection_utils.get_collection_versions_list(namespace=namespace, name=name)
    return jsonify({
        'results': versions
    })


@app.route('/api/v3/collections/<namespace>/<name>/versions/<version>/', methods=['GET'])
@app.route('/api/v3/plugin/ansible/content/published/collections/index/<namespace>/<name>/versions/<version>/', methods=['GET'])
def v3_collection_version_detail(namespace, name, version):
    detail = collection_utils.get_collection_version_detail(namespace=namespace, name=name, version=version)
    return jsonify(detail)



@app.route('/api/v3/plugin/ansible/content/published/collections/artifacts/<tarball>', methods=['GET'])
def v3_collection_artifacts(tarball):

    # init the pulpcore client
    pc = PulpCoreClient()

    try:
        # Stream the request from the external server
        r = pc.get_filename_download_stream(tarball)

        # Check if the request was successful
        if r.status_code != 200:
            return Response(f"Failed to fetch file: {r.status_code}", status=r.status_code)

        # Stream the response to the client
        return Response(
            stream_with_context(r.iter_content(chunk_size=8192)),
            content_type=r.headers.get('Content-Type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename="{tarball}"'
            }
        )
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
