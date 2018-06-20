import urllib

from yas_openstack import Client


class ServerManager(Client):

    def __init__(self):
        super().__init__()
        self.default_image_name = self.create_server_defaults.get('image_name')
        self.default_flavor_name = self.create_server_defaults.get('flavor_name')
        self.default_nics = self.create_server_defaults.get('nics')
        self.default_security_groups = self.create_server_defaults.get('security_groups')
        self.default_userdata = self.create_server_defaults.get('userdata')
        self.default_key_name = self.create_server_defaults.get('key_name')

    def search_for_current_image(self, name):
        images = [image for image in self.image.images()
                  if image.name.startswith(name) and 'current' in image.tags]
        try:
            return images[0].id
        except IndexError:
            raise Exception(f"Found no images with a name starting with {name} tagged as current")

    def find_image_by_name(self, image_name):
        if image_name:
            return self.image.find_image(image_name).id

    def find_flavor_by_name(self, flavor_name):
        return self.compute.find_flavor(flavor_name).id

    def create(self, name, **kwargs):
        image_id = self.find_image_by_name(kwargs.get('image')) or \
                   self.search_for_current_image(self.default_image_name)
        flavor_id = kwargs.get('flavor') or self.find_flavor_by_name(self.default_flavor_name)
        # security_groups = kwargs.get('security_groups') or self.default_security_groups
        userdata = kwargs.get('userdata') or self.default_userdata
        key_name = kwargs.get('key_name') or self.default_key_name
        nics = kwargs.get('nics') or self.default_nics
        meta = kwargs.get('meta')
        description = kwargs.get('description') or ''

        created_server = self.servers.create(
            name=name,
            image=image_id,
            flavor=flavor_id,
            userdata=userdata,
            key_name=key_name,
            nics=nics,
            meta=meta,
            description=description
        )
        return created_server

    def delete(self, server, webhook):
        if webhook:
            query_params = {**dict(server=server.to_dict()), **webhook.get('params', {})}
            encoded_query = urllib.parse.urlencode(query_params)
            uri = webhook['url'] + '?' + encoded_query
            request = urllib.request.Request(uri, method='POST')
            urllib.request.urlopen(request)
        else:
            server = self.servers.get(server.id)
            server.delete()

    def find(self, detailed=True, metadata=None, **kwargs):
        servers = self.findall(detailed=detailed, metadata=metadata, **kwargs)

        if not servers:
            raise NoServersFound

        if len(servers) > 1:
            raise MultipleServersFound(servers)

        return servers[0]

    def findall(self, detailed=True, metadata=None, **kwargs):
        servers = self.servers.list(detailed=detailed, search_opts=kwargs)

        def metadata_filter(server, criteria=metadata):
            results = []
            for criterion in criteria:
                result = server.metadata.get(criterion.lstrip('!')) == criteria[criterion]
                if criterion.startswith('!'):
                    results.append(not result)
                else:
                    results.append(result)
            return all(results)

        if metadata:
            filtered_results = [server for server in servers if metadata_filter(server)]
        else:
            filtered_results = servers

        return filtered_results

    # pylint: disable=no-self-use
    def parse_search_args(self, raw_metadata='', raw_search_opts=''):
        try:
            search_opts = dict(opt.split('=') for opt in (raw_search_opts or '').split(',') if not opt == '')
        except ValueError:
            raise SearchOptionParseError

        try:
            metadata = dict(opt.split('=') for opt in (raw_metadata or '').split(',') if not opt == '')
        except ValueError:
            raise SearchOptionParseError

        search_opts['metadata'] = metadata

        return search_opts


class SearchOptionParseError(Exception):
    def __init__(self):
        super().__init__(
            'Invalid search opts, request must look like  '
            '```<verb>[ search_opts <sort query>=<argument>[,<query>=<argument>[,...]]'
            '[ meta[data] <key>=<value>[,<key>=<value>]]```\n'
            'For example:\n&gt; list search_opts state=Running metadata owner=tswift\n'
            'Available sort queries and fields may be found in the '
            # pylint: disable=line-too-long
            '<https://developer.openstack.org/api-ref/compute/?expanded=list-servers-detailed-detail#list-servers-detailed|docs>.')

class ServersFoundException(Exception):
    pass


class NoServersFound(ServersFoundException):
    def __init__(self):
        super().__init__(
            'No servers found matching the specified search options. Refer to '
            '<https://developer.openstack.org/api-ref/compute/?expanded=list-servers-detail#id4|the docs> '
            'for available search parameters.')


class MultipleServersFound(ServersFoundException):
    def __init__(self, servers):
        super().__init__('\n'.join(
            [f'Found multiple servers: {", ".join([str(dict(name=server.name, id=server.id)) for server in servers])}',
             '',
             'Refer to '
             '<https://developer.openstack.org/api-ref/compute/?expanded=list-servers-detail#id4|the docs> '
             'for available search parameters to make your query more specific.']))
