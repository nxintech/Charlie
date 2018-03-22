import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook import Playbook
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    result = None

    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        host = result._host
        self.result = { host.name: result._result }


Options = namedtuple(
    'Options',
    ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check', 'diff'])


class Runner:
    def __init__(self, hosts):
        self.loader = DataLoader()
        self.inventory = InventoryManager(loader=self.loader, sources=[hosts])
        self.variable_manager = VariableManager(
            loader=self.loader, inventory=self.inventory
        )
        self.options = None
        self.callback = ResultCallback()

    def set_module_path(self, path):
        self.options = Options(
            connection='smart', module_path=path, forks=10, become=None, become_method=None,
            become_user=None, check=False, diff=False)

    def set_extra_vars(self, extra_vars):
        self.variable_manager.extra_vars = extra_vars

    def run(self, playbook):
        pb = Playbook.load(playbook, variable_manager=self.variable_manager, loader=self.loader)
        # only support one playbook.yml
        play = pb.get_plays()[0]

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords={'conn_pass': None, 'become_pass': None},
                stdout_callback=self.callback,
            )
            return tqm.run(play), self.callback.result
        finally:
            if tqm is not None:
                tqm.cleanup()
