import ast
import json
import argparse
from collections import namedtuple
from ansible.vars.manager import VariableManager
from ansible.plugins.callback import CallbackBase
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager


# http://docs.ansible.com/ansible/latest/dev_guide/developing_api.html


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
        print(json.dumps({host.name: result._result}, indent=4))


Options = namedtuple('Options', [
    'sudo', 'su', 'sudo_user', 'su_user',
    'listtags', 'listtasks', 'listhosts',
    'syntax', 'check',
    'ask_pass', 'ask_su_pass', 'ask_sudo_pass', 'ask_vault_pass',
    'connection', 'timeout', 'remote_user', 'private_key_file',
    'module_path', 'forks',
    'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args',
    'become', 'become_method', 'become_user',
    'verbosity', 'diff'])


class PlayBook(object):
    def __init__(self, inventory, extra_vars=None):
        self.pbex = None

        # initialize needed objects
        self.loader = DataLoader()
        self.options = Options(
            sudo=False, su=False, sudo_user=None, su_user=None,
            listtags=False, listtasks=False, listhosts=False,
            syntax=False, check=False,
            ask_pass=False, ask_su_pass=False, ask_sudo_pass=False, ask_vault_pass=False,
            connection='smart', timeout=10, remote_user=None, private_key_file=None,
            ssh_common_args=None, ssh_extra_args=None,
            sftp_extra_args=None, scp_extra_args=None,
            module_path=None, forks=10,
            become=False, become_method='sudo', become_user=None,
            verbosity=0, diff=None)

        # Instantiate our ResultCallback for handling results as they come in
        self.results_callback = ResultCallback()

        # create inventory and pass to var manager
        self.inventory = InventoryManager(loader=self.loader, sources=[inventory])
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.variable_manager.extra_vars = extra_vars
        # passwords = dict(vault_pass='secret')

    def run(self, playbook):
        self.pbex = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=self.options,
            passwords={'conn_pass': None, 'become_pass': None})
        self.pbex._tqm._stdout_callback = ResultCallback()
        return self.pbex.run()


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
    print(pb.run(args.playbook))