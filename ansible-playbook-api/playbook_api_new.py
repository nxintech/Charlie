import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase


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
        return result


Options = namedtuple(
    'Options',
    ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'diff'])
options = Options(
    connection='smart', module_path='/path/to/mymodules', forks=10, become=None, become_method=None,
    become_user=None, check=False, diff=False)


class Runner:
    def __init__(self):
        self.loader = DataLoader()
        self.inventory = None
        self.variable_manager = None

    def set_hosts(self, hosts):
        self.inventory = InventoryManager(loader=self.loader, sources=[hosts])
        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory
        )

    def set_extra_vars(self, extra_vars):
        self.variable_manager.extra_vars = extra_vars

    def run(self, playbook):
        play = Play().load(
            self.loader.load_from_file(playbook),
            variable_manager=self.variable_manager,
            loader=self.loader
        )

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=options,
                passwords={'conn_pass': None, 'become_pass': None},
                stdout_callback=ResultCallback(),
            )
            return tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()
