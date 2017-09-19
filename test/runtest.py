# -*- coding:utf-8 -*- 

from __future__ import absolute_import

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import unittest

from .btree_test import MemBTreeTest, DiskBTreeTest

if __name__ == '__main__':
	unittest.main()