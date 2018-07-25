============
YasOpenstack
============
A `Yas`_ Client for managing OpenStack instances.

Features
--------
- Provides a library of commands for managing OpenStack VMs via Slack.

Commands
--------

+------------+------------------------------------+--------------+-------------------------------------------------------+
| Command    | Aliases                            | Arguments    | Description                                           |
+============+====================================+==============+=======================================================+
| create     | launch, start                      | {{ name }}   | Launches an OpenStack VM                              |
+------------+------------------------------------+--------------+-------------------------------------------------------+
| delete     | drop, terminate, bust a cap in     | {{ names }}  | Deletes one/more OpenStack VMs. Use spaces not commas.|
+------------+------------------------------------+--------------+-------------------------------------------------------+
| list       | N/A                                | N/A          | Lists you OpenStack VMs.*                             |
+------------+------------------------------------+--------------+-------------------------------------------------------+
| list all   | N/A                                | N/A          | Lists all OpenStack VMs.*                             |
+------------+------------------------------------+--------------+-------------------------------------------------------+
| help*      | N/A                                | N/A          | Coming soon: will print a list of available commands. |
+------------+------------------------------------+--------------+-------------------------------------------------------+

\* *By default `list` returns only the name(s) of the instance(s). Add "verbose" to retrieve IP addresses, owners, and statuses.*

Creating or Updating Commands
-----------------------------

+---------------------------------------+--------------------------------------------------------------------------+
| **Step 1:** Setup                     | Clone `yas`_, `YasOpenstack`_, and `YasExampleHandlers`_.                |
+---------------------------------------+--------------------------------------------------------------------------+
| **Step 2:** Make changes              | To introduce a **new command** create a handler. To alter an             |
|                                       | **existing command** find and edit its handler.                          |
+---------------------------------------+--------------------------------------------------------------------------+
| **Step 3:** Create a Slackbot         | It's not a good idea to test changes on the bot developers are using.    |
|                                       | If you have Slack admin privileges, you can create your own test bot.    |
|                                       | If you don't, ask someone who does to create a test bot and give you     |
+---------------------------------------+--------------------------------------------------------------------------+
| **Step 4:** Deploy changes            | See section on **How to Deploy** below.                                  |
+---------------------------------------+--------------------------------------------------------------------------+
| **Step 5** Test changes               | Once you have deployed your changes to the test Slackbot it's ready for  |
|                                       | testing. Go to Slack. Try @mytestslackbot {{ the command you changed }}  |
|                                       | Confirm the response is what you expect.                                 |
+---------------------------------------+--------------------------------------------------------------------------+

**How do I create a Slackbot?**

If you have Slack admin privileges you can create your own Slackbot for testing.

1. Go to https://slack.com/apps/manage/custom-integrations
2. Select ``Bots`` and ``Add Configuration``.
3. Give your bot a name and click ``Create``.
4. Make note of the bot’s name and its auto-generated API Token. You’ll need these later.


Deploying
---------

**Deploying to a test Slackbot**

Copy three files from ``bot.example.com`` to your local Vagrant directory:

.. code:: bash

    # Do this from your local machine
    scp bot.example.com:~/yas.yml .
    scp bot.example.com:~/openstack.yml .
    scp bot.example.com:~/default-userdata.sh .

Edit your local copy of ``yas.yml``. Change the ``bot_name`` and ``slack_app_token`` to be the name and API token of your test Slackbot:

Launch a local Vagrant instance:

.. code:: bash

    # Do this from your local machine
    cd /yas
    vagrant up
    vagrant ssh

Install yas and YasOpenstack:

.. code:: bash

    # Do this from within the VM
    # Within the VM use /vagrant where you'd use /yas
    pip install -U /srv/YasOpenstack/ vagrant

Copy the yml files from earlier into the yas install directory:

.. code:: bash

    # Do this from within the VM
    # Be sure you do it AFTER running pip install, else these files will be overwritten!
    cp /vagrant/yas.yml /vagrant/openstack.yml /vagrant/default-userdata.sh /usr/local/lib/pyenv/versions/3.6.0/etc/yas/

Finally, restart yas ad check the log output to confirm your Slackbot came up without error:

.. code:: bash

    # Do this from within the VM
    sudo systemctl restart yas
    journalctl -xaefu yas

**Deploying to the "production" Slackbot**

Deploying to the "production" Slackbot is a lot easier. Note: our "production" OpenStack Slackbot, @openstack, is hosted on ``bot.example.com``. You will need admin privileges to access this box.

SSH to the cloud instance where the OpenStack Slackbot @openstack is hosted:

.. code:: bash

    # Do this from your local machine
    # You may need to specify a username like bwayne@bot.example.com
    ssh bot.example.com

Execute the following:

.. code:: bash

    # Do this from bot.example.com
    (cd YasOpenstack/; git pull) && (cd yas; git pull)
     && pip install -U YasOpenstack/ yas/
     && cp yas.yml openstack.yml /usr/local/lib/pyenv/versions/3.6.0/etc/yas/
     && sudo systemctl restart yas

.. _Yas: https://github.com/refinery29/yas
.. _yas: https://github.com/refinery29/yas
.. _YasOpenstack: https://github.com/refinery29/YasOpenstack
.. _YasExampleHandlers: https://github.com/schlueter/YasExampleHandlers


Troubleshooting
---------------

Here are several issues you may encounter, along with possible diagnoses.

.. code:: bash

    ImportError: No module named 'foo_handler'

    # You may have made a typo or path error. Look at the handlers_list in yas.yml.
    # Is the path provided for foo_handler accurate? For example, did you write
    # yas.foo_handler when foo_handler.py is in /yas/handlers?

.. code:: bash

    TypeError: __init__() takes 2 positional arguments but 3 were given

    # For those new to Python: self is always the first argument in an instance method
    # and it refers to the class. So if you see __init__(self, a, b) and you attempt
    # to create SomeClass(a, b, c) you will see this error.

.. code:: bash

    AttributeError: 'YamlConfiguration' object has no attribute 'foo'

    # There may be multiple YamlConfigurations in play. Either you have unintentionally
    # referenced the wrong one or the attribute you want isn't defined (or both).
    # Consider this: some configurations might be stored on the FizzHandler which
    # defines self.config. In classes that extend the FizzHandler you would use
    # self.config.foo to access foo. Some other configurations might be stored on the
    # BuzzClient. Maybe the BuzzClient doesn't have a self.config; its attributes are
    # stored independently. You would use self.foo rather than self.config.foo.

.. code:: bash

    DiscoveryFailure: Could not determine a suitable URL for the plugin

    # You may have forgotten to overwrite the default value for auth_url in the
    # installed copy of YasOpenstack. Did you cp openstack.yml into the
    # /usr/local/lib/pyenv/versions/3.6.0/etc/yas/ directory?

----

:Author: Brandon Schlueter <yas@schlueter.blue>
:Copyright: Brandon Schlueter 2017
:License: Affero General Public License v3 or newer
