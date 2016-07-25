"""
ref https://gist.github.com/agaffney/0d026372aa0f1966f340,
https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/hipchat.py
"""

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default


class CallbackModule(CallbackModule_default):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'human_log'
    
    def __init__(self):
        super(CallbackModule, self).__init__()
        self.returns = {}
        self.current_task = None

    def parse_result(self, result):
        return dict(
            host=result._host,
            failed=result.is_failed(),
            msg=result._result['msg'])

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        self.returns['play_name'] = name
        print("playbook '{0}' start".format(name))
    
    def v2_playbook_on_task_start(self, task, is_conditional):
        self.current_task = task.get_name().strip()
        print("task '{0}' start".format(self.current_task))

    def v2_runner_on_failed(self, result, ignore_errors=False):
         self.returns[self.current_task] = self.parse_result(result)
    
    def v2_runner_on_ok(self, result):
        if result._result.get('changed', False):
            self.returns[self.current_task] = self.parse_result(result)
        else:
            pass

    def v2_runner_on_unreachable(self, result):
        # do sth
        pass

    def v2_runner_on_skipped(self, result):
        pass

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_item_on_ok(self, result):
        pass

    def v2_playbook_item_on_skipped(self, result):
        pass

    def v2_playbook_item_on_failed(self, result):
        pass

    def human_log(self):
        """ wirte self.returns to somewhrere insdead of print it """
        print(self.returns)
