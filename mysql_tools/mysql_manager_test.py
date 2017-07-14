# -*- coding:utf-8 -*-
from .mysql_manager import *
from unittest import TestCase


class TestGrant(TestCase):
    @classmethod
    def setUpClass(cls):
        ins = Instance('localhost', 3306, '5.6')
        ins.add_database("test")
        ins.role = 'master'
        cls.ins = ins

    def test_grant(self):
        self.ins.grant(['select', 'update'], 'test', '*', 'user', '192.168.0.1')
        print(self.ins.grants)
