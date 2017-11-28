from pygtrie import StringTrie

import unittest


def foo():
    print('foo')


def bar():
    print('bar')


class TestTrie(unittest.TestCase):
    def setUp(self):
        pass

    def test_(self):
        tree = StringTrie()
        tree['/foo'] = foo
        tree['/bar'] = bar
        tree['/foo/test'] = lambda x: print('test')
        tree['/foo/txxt'] = lambda x: print('txxt')
        tree['/foo/text'] = lambda x: print('text')

        # print(tree.keys())

        print(tree.has_subtrie('/bar'))