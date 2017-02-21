# Copyright 2017 Brandon Schlueter
# pylint: disable=no-self-use

import os

from flask import Flask
from flask_restful import reqparse, Api, Resource

from novaclient import client

# 2.38 is the highest valid version as of date of commit
OS_COMPUTE_VERSION = os.environ.get('OS_COMPUTE_VERSION', '2.38')
OS_USERNAME = os.environ.get('OS_USERNAME')
OS_PASSWORD = os.environ.get('OS_PASSWORD')
OS_PROJECT_NAME = os.environ.get('OS_PROJECT_NAME')
OS_AUTH_URL = os.environ.get('OS_AUTH_URL')
OS_PROJECT_DOMAIN_NAME = os.environ.get('OS_PROJECT_DOMAIN_NAME', 'default')
OS_USER_DOMAIN_NAME = os.environ.get('OS_USER_DOMAIN_NAME', 'default')

NOVA = client.Client(version=OS_COMPUTE_VERSION,
                     username=OS_USERNAME,
                     password=OS_PASSWORD,
                     project_name=OS_PROJECT_NAME,
                     auth_url=OS_AUTH_URL,
                     project_domain_name=OS_PROJECT_DOMAIN_NAME,
                     user_domain_name=OS_USER_DOMAIN_NAME)

class Ping(Resource):
    def get(self):
        return {"response": "pong"}

class Server(Resource):
    def post(self, name, creator):
        server = NOVA.servers.create(
            name=name,
            image=NOVA.glance.find_image('ubuntu/trusty64'),
            flavor=[flavor for flavor in NOVA.flavors.list() if flavor.name == 'm1.big'],
            # TODO requires neutron client
            security_groups=['344188ea-7747-4a67-8517-743e99799fda'],
            userdata='',
            key_name='bs',
            # TODO requires neutron client
            nics=[{
                "net-id": '832bbfef-7ebd-4da5-8029-f7cf89e4ee5e',
                "v4-fixed-ip": ''
            }]
        )
        server.tag('creator={}'.format(creator))

        return '', 202

    def delete(self, name):
        server = [server for server in NOVA.servers.list() if server.name == name][0]
        server.delete()
        return '', 204

class ServerList(Resource):
    def get(self):
        return [server.to_dict() for server in NOVA.servers.list()], 200

def initialize_application():

    app = Flask(__name__)
    api = Api(app)

    parser = reqparse.RequestParser()
    parser.add_argument('task')

    api.add_resource(Ping, '/ping')
    api.add_resource(ServerList, '/server/list')

    app.run(debug=True)
