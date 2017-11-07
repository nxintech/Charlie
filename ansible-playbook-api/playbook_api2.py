# -*- coding:utf-8 -*-

from __future__ import print_function
import ast
import argparse
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.plugins.callback import CallbackBase
from ansible.executor.playbook_executor import PlaybookExecutor


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in
    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result
        This method could store the result in an instance attribute for retrieval later
        """
        host = result._host
        print({host.name: result._result}, indent=4)


Options = namedtuple('Options', [
    # must applied attributes
    'listtags', 'listtasks', 'listhosts', 'syntax', 'subset', 'module_path', 'become', 'become_user', 'become_method',
    # user defined attributes
    'private_key_file', 'connection', 'forks', 'timeout', 'verbosity', 'check'
])


class PlayBook(object):
    def __init__(self, inventory='/etc/ansible/hosts', extra_vars=None, private_key_file=None):
        """
        :param playbook: playbook.yml
        :param inventory: inventory file or script
        :type param extra_vars: dict
        :param private_key_file: ssh private key
        """
        self.pbex = None
        self.options = Options(private_key_file=private_key_file, connection='smart', forks=10, timeout=10,
                               verbosity=0, check=False,
                               listtasks=False, listhosts=False, syntax=False,
                               subset=None, module_path=None, become=None, become_user=None, become_method='sudo')

        # initialize needed objects
        self.loader = DataLoader()
        self.variable_manager = VariableManager()
        self.variable_manager.extra_vars = extra_vars
        self.variable_manager.options_vars = {'ansible_check_mode': self.options.check}
        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=inventory)
        self.variable_manager.set_inventory(self.inventory)
        # Limits inventory results to a subset of inventory that matches a given pattern
        self.inventory._subset = self.options.subset

    def run_playbook(self, playbook):
        self.pbex = PlaybookExecutor(playbooks=[playbook], inventory=self.inventory,
                                     variable_manager=self.variable_manager,
                                     loader=self.loader, options=self.options,
                                     passwords={'conn_pass': None, 'become_pass': None})
        self.pbex._tqm._stdout_callback = ResultCallback()
        return self.pbex.run()

    def run_play(self, play):
        pass


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="""
ansible Playbook API. Usage:
    playbook_api -i /etc/ansible/hosts -e {'key': 'value'} test.yaml

    Notice :key and value in extra-vars must in __single quotation__
""")
parser.add_argument('-i', '--inventory', default='/etc/ansible/hosts', help='ansible playbook inventory')
parser.add_argument('-e', '--extra-vars', default={}, type=ast.literal_eval, help='playbook extra-vars')
parser.add_argument('playbook', help='ansible playbook yaml file')

if __name__ == '__main__':
    args = parser.parse_args()
    pb = PlayBook(inventory=args.inventory, extra_vars=args.extra_vars)
    print(pb.run_playbook(args.playbook))


