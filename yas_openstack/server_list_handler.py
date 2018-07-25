from pprint import pformat

from jinja2 import Template

from yas_openstack.openstack_handler import OpenStackHandler


class OpenStackServerListHandler(OpenStackHandler):
    """Lists your OpenStack instances.
    Use `list all` to get a list of everyone's' instances.
    Add `verbose` to get more information like IP, status, and owner.
    """
    triggers = ['list']

    def __init__(self, bot):
        super().__init__(r'(?:list)(?: +(all))?'
                         r'(?: search_opts (' + self.SEARCH_OPTS_REGEX + '))?'
                         r'(?: meta(?:data)? (!?' + self.SEARCH_OPTS_REGEX + '))?',
                         bot)

    def get_default_search_options(self, data):
        raw_default_search_options = Template(self.config.default_search_opts).render(**data)
        raw_default_search_metadata = Template(self.config.default_search_metadata).render(**data)
        default_search_options = dict(opt.split('=') for opt in raw_default_search_options.split(',') if not opt == '')
        default_search_options['metadata'] = dict(
            opt.split('=')
            for opt in raw_default_search_metadata.split(',')
            if not opt == '')
        return default_search_options

    def handle(self, data, reply):
        modifier, raw_search_opts, raw_metadata = self.current_match.groups()
        self.bot.log.debug(f"{data['yas_hash']} raw_search_opts: {raw_search_opts} "
                 "and raw_metadata: {raw_metadata} and modifier: {modifier}")

        raw_default_search_opts = Template(self.config.default_search_opts).render(**data)
        raw_default_search_metadata = Template(self.config.default_search_metadata).render(**data)

        if type(modifier) == str and modifier.lower() == 'all':
            search_opts = dict(metadata={})
        else:
            search_opts = self.server_manager.parse_search_args(
                raw_metadata=raw_metadata if raw_search_opts or raw_metadata else raw_default_search_metadata,
                raw_search_opts=raw_search_opts if raw_search_opts or raw_metadata else raw_default_search_opts)

        servers = self.server_manager.findall(**search_opts)
        verbose = 'verbose' in data['text'].lower().split(' ')

        attachments = [
            self.parse_server_to_attachment(
                server.to_dict(),
                search_opts['metadata'],
                verbose)
            for server in servers
        ]

        options = {**search_opts, **search_opts['metadata']}
        option_string = ", ".join([opt + "=" + options[opt] for opt in options if isinstance(options[opt], str)])

        reply(f"Found {len(servers)} instances:")
        while attachments:
            self.bot.api_call('chat.postMessage',
                              channel=data['channel'],
                              attachments=attachments[:20])
            attachments = attachments[20:]

    def parse_server_to_attachment(self, server, metadata, verbose):

        self.bot.log.debug(f"Parsing server:\n{pformat(server)}")
        addresses = [interface['addr']
                     for network in server['addresses']
                     for interface in server['addresses'][network]]

        init = server['metadata'].get('init')
        test = server['metadata'].get('test')

        if init == 'done':
            if test in ['pass', 'skipped']:
                attachment_color = '#7D7'
            elif test in ['full', 'quick', 'started']:
                attachment_color = '#AEC6CF'
            elif test == 'fail':
                attachment_color = '#FF3'
            else:
                attachment_color = '#AAA'
        elif init == 'started':
            attachment_color = '#AEC6CF'
        elif init == 'fail':
            attachment_color = '#C23B22'
        else:
            attachment_color = '#AAA'

        for key in ['owner_id']:
            server['metadata'].pop(key, None)

        if 'owner_id' in metadata:
            # Add empty owner to remove from output
            metadata['owner'] = None

        if verbose:
            fields = [dict(title=key, value=server['metadata'][key], short=True)
                      for key in server['metadata'] if not key in metadata and server['metadata'][key]]
            fields.append(dict(title='addresses', value=', '.join(addresses), short=len(addresses) == 1))
            fields.append(dict(title='id', value=server['id'], short=False))
        else:
            fields = []

        return dict(
            title=f"{server['name']}.{self.config.domain} from image {server['id']}",
            title_link=f"http://www.{server['name']}.{self.config.domain}",
            fields=fields,
            color=attachment_color)
