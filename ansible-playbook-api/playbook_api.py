# -*- coding:utf-8 -*-

# for ansible 2.0+

import os
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor


Options = namedtuple('Options', [
    'inventory',
    'sudo', 'su', 'sudo_user', 'su_user',
    'listtags', 'listtasks', 'listhosts',
    'syntax', 'check',
    'ask_pass', 'ask_su_pass', 'ask_sudo_pass', 'ask_vault_pass',
    'connection', 'timeout', 'remote_user', 'private_key_file',
    'module_path', 'forks',
    'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args',
    'become', 'become_method', 'become_user',
    'verbosity'])


class PlayBook(object):
    def __init__(self, playbook, inventory="inventory.py", extra_vars=None):
        basedir = os.path.abspath(os.path.dirname(__file__))
        self.playbook = os.path.join(basedir, playbook)
        self.options = Options(
            inventory=inventory,
            sudo=False, su=False, sudo_user=None, su_user=None,
            listtags=False, listtasks=False, listhosts=False,
            syntax=False, check=False,
            ask_pass=False,ask_su_pass=False,ask_sudo_pass=False,ask_vault_pass=False,
            connection='smart', timeout=10, remote_user=None, private_key_file=None,
            ssh_common_args=None, ssh_extra_args=None,
            sftp_extra_args=None, scp_extra_args=None,
            module_path=None, forks=5,
            become=False, become_method='sudo', become_user=None,
            verbosity=0)
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
