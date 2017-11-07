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
    'connection', 'forks', 'become', 'become_method', 'become_user', 'check', 'diff'])


class PlayBook(object):
    def __init__(self, inventory, extra_vars=None):
        self.pbex = None

        # initialize needed objects
        self.loader = DataLoader()
        self.options = Options(
            connection='smart',
            # module_path='/path/to/mymodules',
            forks=100,
            become=None,
            become_method=None,
            become_user=None,
            check=False,
            diff=False)

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
    print(pb.run_playbook(args.playbook))