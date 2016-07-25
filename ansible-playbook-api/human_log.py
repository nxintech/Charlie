"""
ref https://gist.github.com/agaffney/0d026372aa0f1966f340,
https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/hipchat.py
"""

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default

class CallbackModule(CallbackModule_default):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'human_log'

    def v2_playbook_on_task_start(self, task, is_conditional):
        pass

    def v2_runner_on_failed(self, result, ignore_errors=False):
        # do sth
        super(CallbackModule, self)
    
    def v2_runner_on_ok(self, result):
        if result._result.get('changed', False):
            # do sth
            super(CallbackModule, self).v2_runner_on_ok(result)
        else:
            pass

    def v2_runner_on_unreachable(self, result):
        # do sth
        super(CallbackModule, self).v2_runner_on_unreachable(result)

    def v2_runner_on_skipped(self, result):
        pass

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_item_on_ok(self, result):
        super(CallbackModule, self).v2_playbook_item_on_ok(result)

    def v2_playbook_item_on_skipped(self, result):
        pass

    def v2_playbook_item_on_failed(self, result):
        super(CallbackModule, self).v2_playbook_item_on_failed(result)
