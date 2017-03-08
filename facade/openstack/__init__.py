import os
from collections import namedtuple

from novaclient.client import Client as NovaClient

from facade.openstack.yaml_file_config import YamlConfiguration

config = YamlConfiguration()

class Client:
    def __init__(self):
        self._novaclient = NovaClient(
            version=config.compute_version,
            username=config.username,
            password=config.password,
            project_name=config.project_name,
            auth_url=config.auth_url,
            project_domain_name=config.project_domain_name,
            user_domain_name=config.user_domain_name
        )
        self.create_server_defaults = config.create_server_defaults
        self.servers = self._novaclient.servers
