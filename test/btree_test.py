# -*- coding:utf-8 -*- 

from __future__ import absolute_import

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import os
import sys
import random
import unittest

from btree import MemBTree, DiskBTree

class MemBTreeTest(unittest.TestCase):

    def get_num(self):
        return int(random.random()*10000000)

    def random_insert(self, tree, length=10, doc=None):
        seq = set()
        while len(seq) != length:
            seq.add(self.get_num())
        seq = list(seq)

        random.shuffle(seq)
        for num in seq:
            tree.insert(num)
        return seq

    def random_search(self, tree, seq):
        random.shuffle(seq)
        for num in seq:
            node, _ = tree.search(num)
            self.assertIsNotNone(node)
            tree.remove(num)
            node, _ = tree.search(num)
            self.assertIsNone(node)

    def test_degree3(self):
        tree = MemBTree(3)
        seq = self.random_insert(tree, 40000)
        self.random_search(tree, seq)
        self.assertEqual(tree.root.num, 0)

    def test_degree5(self):
        tree = MemBTree(5)
        seq = self.random_insert(tree, 60000)
        self.random_search(tree, seq)
        self.assertEqual(tree.root.num, 0)

    def test_degree7(self):
        tree = MemBTree(7)
        seq = self.random_insert(tree, 80000)
        self.random_search(tree, seq)
        self.assertEqual(tree.root.num, 0)

    def test_random_degree(self):
        tree = MemBTree(int(random.random()*100))
        seq = self.random_insert(tree, 100000)
        self.random_search(tree, seq)
        self.assertEqual(tree.root.num, 0)

    def test_insert(self):
        tree = MemBTree(int(random.random()*100))

        seq = self.random_insert(tree, 60000)
        
        key = seq[23333]
        tree.remove(key)
        del seq[23333]

        value = "Unittest_{0}".format(key)
        tree.insert(key, value)

        self.random_search(tree, seq)

        self.assertEqual(tree.select(key), [value])

    def test_update(self):
        pass

    def test_insert_exception(self):
        pass


class DiskBTreeTest(unittest.TestCase):

    def tearDown(self):
        os.system("rm -rf fsunittest")

    def get_num(self):
        return int(random.random()*10000000)

    def random_insert(self, tree, length=10, doc=None):
        seq = set()
        while len(seq) != length:
            seq.add(self.get_num())
        seq = list(seq)

        random.shuffle(seq)
        for num in seq:
            tree.insert(num)
        return seq

    def random_search(self, tree, seq):
        random.shuffle(seq)
        for num in seq:
            node, _ = tree.search(num)
            self.assertIsNotNone(node)
            tree.remove(num)
            node, _ = tree.search(num)
            self.assertIsNone(node)

    def test_degree3(self):
        tree = DiskBTree(3, "fsunittest")
        seq = self.random_insert(tree, 100)
        self.random_search(tree, seq)
        self.assertEqual(tree.root.num, 0)

    def test_random_degree(self):
        tree = DiskBTree(int(random.random()*100), "fsunittest")
        seq = self.random_insert(tree, 1000)
        self.random_search(tree, seq)
        self.assertEqual(tree.root.num, 0)

    def test_insert(self):
        tree = DiskBTree(int(random.random()*100), "fsunittest")

        seq = self.random_insert(tree, 1000)
        
        key = seq[233]
        tree.remove(key)
        del seq[233]

        value = "Unittest_{0}".format(key)
        tree.insert(key, value)

        self.random_search(tree, seq)

        self.assertEqual(tree.select(key), [value])

    def test_update(self):
        pass

    def test_insert_exception(self):
        pass

