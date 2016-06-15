# -*- coding:utf-8 -*-

# for ansible 2.0+

import os
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor


class Options(object):
    """
    Options class to replace Ansible OptParser
    """

    def __init__(self, inventory=None, extra_vars=None):
        self.inventory = inventory
        self.extra_vars = extra_vars

        # dry-run
        self.check = False  # must be False, otherwise playbook wont actually run
        self.diff = None
        self.syntax = None

        # connection
        self.connection = "smart"  # or "ssh"
        self.ask_pass = False
        self.private_key_file = None
        self.remote_user = None
        self.timeout = 10

        # su
        self.su = False
        self.su_user = None
        self.ask_su_pass = False

        # sudo
        self.sudo = False
        self.sudo_user = None
        self.ask_sudo_pass = False

        # become
        self.become = False
        self.become_method = "sudo"
        self.become_user = None
        self.become_ask_pass = None

        # ansible-vault
        self.ask_vault_pass = False
        self.vault_password_files = None
        self.new_vault_password_file = None

        # list
        self.listhosts = None
        self.listtasks = None
        self.listtags = None

        # tags
        self.tags = "all"
        self.skip_tags = None

        # args
        self.ssh_common_args = ""
        self.sftp_extra_args = ""
        self.scp_extra_args = ""
        self.ssh_extra_args = ""

        self.force_handlers = None
        self.flush_cache = None
        self.module_path = None
        self.subset = None
        self.verbosity = 0
        self.forks = 5
        self.output_file = None


class PlayBook(object):
    def __init__(self, playbook, inventory="inventory.py", extra_vars=None):
        self.playbook = "%s/%s" % (os.path.dirname(__file__), playbook)
        self.options = Options(inventory, extra_vars)
        self.loader = DataLoader()
        self.variable_manager = VariableManager()
        self.variable_manager.set_inventory(self.options.inventory)
        self.inventory = Inventory(loader=self.loader,
                                   variable_manager=self.variable_manager,
                                   host_list=self.options.inventory)
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
