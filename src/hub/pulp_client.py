import json
import os
import requests
import time
from logzero import logger

from pprint import pprint

"""
/pulp/api/v3/distributions/file/file/
/pulp/api/v3/remotes/file/file/
/pulp/api/v3/content/file/files/
/pulp/api/v3/publications/file/file/
/pulp/api/v3/repositories/file/file/
/pulp/api/v3/repositories/file/file/<repository_pk>/
/pulp/api/v3/repositories/file/file/<repository_pk>/versions/
"""


class PulpCoreClient:
    def __init__(self, baseurl=None, username=None, password=None):
        self.baseurl = baseurl or os.environ.get('PULP_CORE_URL')
        self.username = username or os.environ.get('PULP_CORE_USERNAME')
        self.password = password or os.environ.get('PULP_CORE_PASSWORD')

    def get_repositories_map(self):

        repos = {}

        next_url = self.baseurl + '/pulp/api/v3/repositories/file/file/'
        rr = requests.get(
            next_url,
            auth=(self.username, self.password),
            verify=False
        )

        print(rr.json())

        while next_url:
            logger.info(next_url)
            rr = requests.get(
                next_url,
                auth=(self.username, self.password),
                verify=False
            )
            ds = rr.json()
            for repo in ds['results']:
                repos[repo['name']] = repo

            if not ds.get('next'):
                break

            next_url = self.baseurl + ds['next']

        return repos

    def get_distributions_map(self):

        distros = {}

        next_url = self.baseurl + '/pulp/api/v3/distributions/file/file/'
        rr = requests.get(
            next_url,
            auth=(self.username, self.password),
            verify=False
        )

        while next_url:
            logger.info(next_url)
            rr = requests.get(
                next_url,
                auth=(self.username, self.password),
                verify=False
            )
            ds = rr.json()
            for distro in ds['results']:
                distros[distro['name']] = distro

            if not ds.get('next'):
                break

            next_url = self.baseurl + ds['next']

        return distros

    def create_repository(self, repository_name):

        # get the list first ...
        repo_map = self.get_repositories_map()

        if repository_name in repo_map:
            return repo_map[repository_name]

        rr = requests.post(
            self.baseurl + '/pulp/api/v3/repositories/file/file/',
            verify=False,
            auth=(self.username, self.password),
            json={
                'name': repository_name,
                'autopublish': True,
            }
        )

        return rr.json()

    def create_distribution(self, repository_details, distro_name):

        pprint(repository_details)
        logger.info(repository_details)

        distros = self.get_distributions_map()
        if distro_name in distros:
            return distros[distro_name]

        rr = requests.post(
            self.baseurl + '/pulp/api/v3/distributions/file/file/',
            verify=False,
            auth=(self.username, self.password),
            json={
                'name': distro_name,
                'base_path': distro_name,
                'repository': repository_details['pulp_href'],
            }
        )
        task_ds = rr.json()

        return {}

    def upload_file(self, file_path, repository_name=None):

        with open(file_path, 'rb') as f:
            rr = requests.post(
                #self.baseurl + f"/pulp/api/v3/uploads/",
                self.baseurl + f"/pulp/api/v3/content/file/files/",
                auth=(self.username, self.password),
                verify=False,
                files={'file': f},
                data={
                    'relative_path': os.path.basename(file_path),
                    #'size': os.path.getsize(file_path)
                }
            )
        logger.info(rr)
        logger.info(json.dumps(rr.json(), indent=2))

        task_ds = rr.json()
        task_id = task_ds['task']

        pulp_file_data = self.wait_for_task(task_id)
        if repository_name is None:
            return pulp_file_data

        # add it to the repository ...
        repos = self.get_repositories_map()
        repo = repos[repository_name]

        payload = {
            #'repository': repo['pulp_href'],
            'add_content_units': [pulp_file_data['created_resources'][0]],
        }
        rr = requests.post(
            self.baseurl + repo['pulp_href'] + 'modify/',
            auth=(self.username, self.password),
            verify=False,
            json=payload,
        )

        logger.info(json.dumps(rr.json(), indent=2))
        task_ds = rr.json()
        task_id = task_ds['task']
        add_result = self.wait_for_task(task_id)
        logger.info(json.dumps(add_result, indent=2))

        return {
            'pulp_href': pulp_file_data['created_resources'][0],
            'repository': {
                'name': repository_name,
                'pulp_href': repo['pulp_href'],
            }
        }


    def wait_for_task(self, task_id):
        #task_url = self.baseurl + f'/pulp/api/v3/tasks/{task_id}'
        task_url = self.baseurl + task_id
        while True:
            rr = requests.get(
                task_url,
                auth=(self.username, self.password),
                verify=False,
            )
            logger.info(json.dumps(rr.json(), indent=2))

            taskds = rr.json()
            if taskds.get('state') in ['completed', 'failed', 'error']:
                return taskds

            time.sleep(2)

        return {}

    def get_filename_url(self, filename):
        return self.baseurl + f'/pulp/content/hub/{filename}'
        
    def download_file(self, filename, destination):
        #  https://localhost:8444/pulp/content/hub/snagoor-aap_common-1.0.4.tar.gz
        pass

    def get_filename_download_stream(self, filename):
        url = self.get_filename_url(filename)
        rr = requests.get(
            url,
            stream=True,
            auth=(self.username, self.password),
            verify=False,            
        )
        return rr
