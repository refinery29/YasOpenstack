import json
import os
import sys

from jinja2 import Template
from novaclient.exceptions import Forbidden

from yas_openstack.openstack_handler import OpenStackHandler
from yas_openstack.server import ServersFoundException


def _parse_meta(meta_string):
    if meta_string:
        try:
            meta_dict = dict(pair.split('=') for pair in meta_string.split(','))
        except ValueError:
            raise ValueError('Invalid meta, format must be "key=value,key=value..."')
        for key in meta_dict:
            meta_dict[key] = meta_dict[key] or ''
    else:
        meta_dict = {}

    return meta_dict

class OpenStackServerCreateHandler(OpenStackHandler):
    """Launches an OpenStack instance.
    Takes a single argument: the desired name.
    """
    triggers = ['create', 'launch', 'start']

    def __init__(self, bot):
        super().__init__(r'(re)?(?:launch|start|create) ([-a-zA-Z0-9]+)'
                         r'(?: on ([^\ ]+:?[^\ ]+))?'
                         r'(?: meta(?:data)? (' + self.SEARCH_OPTS_REGEX + '))?'
                         r'(?: from ([^\ ]+))?'
                         r'(?: using ([^\ ]+))?',
                         bot)
        self.bot.log.debug(f'Initializing OpenStack server create handler with defaults:\n{self.bot.config.__dict__}')
        self.template = self.get_userdata_template()

    def get_userdata_template(self):
        config_userdata = self.config.create_server_defaults.get('userdata', '')
        potential_userdata_file = os.path.join(sys.prefix, config_userdata)

        if os.path.isfile(potential_userdata_file):
            with open(potential_userdata_file, 'r') as template_file:
                template = template_file.read()
        else:
            template = config_userdata

        return Template(template)

    def handle(self, data, reply):
        recreate, name, branch, meta_string, image, neptune_branch = self.current_match.groups()
        self.bot.log.info(f"Received request for {name} on {branch} from {image}")

        if name.isdigit():
            reply(f'{name} is not a valid hostname. Numbers-only hostnames are not allowed.')

        if recreate == 're':
            try:
                server = self.server_manager.find(name=f'^{name}$')
                self.server_manager.delete(server, None)
            except ServersFoundException:
                reply(f'Could not find existing {name}, ignoring')

        elif self.server_manager.findall(name=f"^{name}$"):
            return reply(f"{name} already exists.")

        meta = _parse_meta(meta_string)

        creator_info = self.bot.retrieve_user_info(data.get('user', ''))

        if creator_info and 'user' in creator_info:
            meta['owner'] = creator_info['user']['name']
        elif not 'owner' in meta:
            meta['owner'] = 'unknown'

        meta['owner_id'] = data.get('user', None) or data.get('bot_id', 'unknown')
        meta['init'] = 'pending'
        meta['branch'] = branch or ''

        template = self.get_userdata_template()
        userdata = template.render(meta=json.dumps(meta),
                                   name=name,
                                   branch=branch or '',
                                   neptune_branch=neptune_branch or \
                                       self.config.create_server_defaults.get('neptune_branch', 'master'),
                                   data=data)
        try:
            server = self.server_manager.create(name, userdata=userdata, image=image, meta=meta)
        except Forbidden as forbidden:
            if "Quota exceeded" in forbidden.message:
                return reply(forbidden.message)
            # pylint: disable=raising-bad-type
            raise forbidden
        reply(f"Starting {name} from image {server.image['id']}")
        self.bot.log.debug(f"Created used userdata:\n{userdata}")
