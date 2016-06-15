# -*- coding:utf-8 -*-

# for ansible 2.0+

import os
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor


Options = namedtuple('Options', [
    'listtags', 'listtasks', 'listhosts',
    'syntax', 'check',
    'connection', 'timeout', 'remote_user', 'private_key_file',
    'module_path', 'forks',
    'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args',
    'become', 'become_method', 'become_user',
    'verbosity'])

options = Options(
    listtags=False, listtasks=False, listhosts=False,
    syntax=False, check=False,

    # connection
    connection='ssh', timeout=10, remote_user=None, private_key_file=None,

    # args
    ssh_common_args=None, ssh_extra_args=None,
    sftp_extra_args=None, scp_extra_args=None,

    module_path=None, forks=5,
    become=True, become_method=None, become_user=None,
    verbosity=None)


class PlayBook(object):
    def __init__(self, playbook, inventory="inventory.py", extra_vars=None):
        self.playbook = "%s/%s" % (os.path.dirname(__file__), playbook)
        self.options = options
        self.loader = DataLoader()
        self.variable_manager = VariableManager()
        self.inventory = Inventory(loader=self.loader,
                                   variable_manager=self.variable_manager,
                                   host_list=inventory)
        self.pbex = PlaybookExecutor(playbooks=[self.playbook],
                                     inventory=self.inventory,
                                     loader=self.loader,
                                     variable_manager=self.variable_manager,
                                     options=self.options,
                                     passwords={'become_pass': None})

    def run(self):
        self.pbex.run()
        stats = self.pbex._tqm._stats
        self.pbex._tqm.send_callback('human_log')
        return stats

if __name__ == "__main__":
    pb = PlayBook("your playbook yaml", inventory="inventory.py", extra_vars=None)
    print(pb.run())
