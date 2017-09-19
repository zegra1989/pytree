# -*- coding:utf-8 -*- 

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import pickle

from fs import FS

class BNode(object):
    def __init__(self, degree):
        super(BNode, self).__init__()
        self.num = 0
        self.isleaf = True
        self.degree = degree
        self.keys = [None for _ in xrange(degree*2-1)]
        self.docs = [[] for _ in xrange(degree*2-1)]
        self.pnodes = [None for _ in xrange(degree*2)]

    def pointer(self):
        raise NotImplementedError()

    def __str__(self):
        return "num:{0} keys:{1} docs:{2}".format(
                    self.num, self.keys[:self.num], self.docs[:self.num]) 


class BTree(object):
    """docstring for BTree"""

    def __init__(self, degree):
        super(BTree, self).__init__()
        self.degree = degree
        self.threshold = degree*2-1
        self.root = self.allocate_node()
        self.save_node(self.root)

    def allocate_node(self):
        raise NotImplementedError()

    def deallocate_node(self, node):
        raise NotImplementedError()

    def save_node(self, node):
        raise NotImplementedError()

    def load_node(self, node, ipos):
        raise NotImplementedError()

    def insert_value(self, node, ipos, doc):
        raise NotImplementedError()

    def update_value(self, node, ipos, doc):
        raise NotImplementedError()

    def insert(self, key, doc=None):
        node, ipos = self.search(key)
        if node is not None:
            raise Exception("Key:{0} has exist!".format(key))

        node, ipos = self.insert2(key)
        return self.insert_value(node, ipos, doc)

    def update(self, key, doc=None):
        node, ipos = self.search(key)
        if node is None:
            node, ipos = self.insert2(key)
            return self.insert_value(node, ipos, doc)
        return self.update_value(node, ipos, doc)

    def select(self, key):
        node, ipos = self.search(key)
        if node is None:
            return None
        return node.docs[ipos]

    def search(self, key, node = None):
        
        if node is None:
            node = self.root

        ipos = 0
        while ipos < node.num and key > node.keys[ipos]:
            ipos += 1

        if ipos < node.num and key == node.keys[ipos]:
            return node, ipos

        if node.isleaf is True:
            return None, -1

        return self.search(key, self.load_node(node, ipos))

    def split(self, parent, ipos, node):

        new_node = self.allocate_node()
        new_node.isleaf = node.isleaf
        for i in xrange(0, self.degree-1):
            new_node.keys[i] = node.keys[i+self.degree]
            new_node.docs[i] = node.docs[i+self.degree]
        new_node.num = node.num = self.degree-1

        if node.isleaf is False:
            for i in xrange(0, self.degree):
                new_node.pnodes[i] = node.pnodes[i+self.degree]

        for i in xrange(parent.num-1, ipos-1, -1):
            # 此处不会越界，因为在 insert 中有保护
            parent.keys[i+1] = parent.keys[i]
            parent.docs[i+1] = parent.docs[i]
        parent.keys[ipos] = node.keys[self.degree-1]
        parent.docs[ipos] = node.docs[self.degree-1]
        parent.num += 1

        for i in xrange(parent.num-1, ipos, -1):
            parent.pnodes[i+1] = parent.pnodes[i]
        parent.pnodes[ipos+1] = new_node.pointer()

        self.save_node(node)
        self.save_node(parent)
        self.save_node(new_node)

    def insert_key(self, node, key):

        ipos = node.num-1
        if node.isleaf is True:

            while ipos >= 0 and key < node.keys[ipos]:
                # 此处不会越界，因为在 insert 中有保护
                node.keys[ipos+1] = node.keys[ipos]
                node.docs[ipos+1] = node.docs[ipos]
                ipos -= 1

            node.keys[ipos+1] = key
            node.num += 1
            return node, ipos+1

        # insert to non-leaf node, search child
        while ipos >= 0 and key < node.keys[ipos]:
            ipos -= 1

        ipos += 1
        child = self.load_node(node, ipos)
        if child.num == self.threshold:
            self.split(node, ipos, child)
            if key > node.keys[ipos]:
                # 被插入的节点为新分裂出来的点
                child = self.load_node(node, ipos+1)
        return self.insert_key(child, key)

    def insert2(self, key):

        if self.root.num != self.threshold:
            return self.insert_key(self.root, key)

        old_root = self.root
        new_root = self.allocate_node()
        new_root.isleaf = False
        new_root.pnodes[0] = old_root.pointer()

        self.root = new_root
        self.split(new_root, 0, old_root)
        return self.insert_key(new_root, key)

    def merge(self, node, ipos):
        """
            将一个key左右两个兄弟合并
            ipos 是 node.keys 中关键词的位置
            ipos 也是 node.pnodes 中 关键词 左孩子的位置
        """

        lchild = self.load_node(node, ipos)
        lchild.keys[lchild.num] = node.keys[ipos]
        lchild.docs[lchild.num] = node.docs[ipos]
        lchild.num += 1

        rchild = self.load_node(node, ipos+1)
        irpos = 0
        while irpos < rchild.num:
            lchild.keys[lchild.num+irpos] = rchild.keys[irpos]
            lchild.docs[lchild.num+irpos] = rchild.docs[irpos]
            lchild.pnodes[lchild.num+irpos] = rchild.pnodes[irpos]
            irpos += 1
        lchild.num += rchild.num
        lchild.pnodes[lchild.num] = rchild.pnodes[rchild.num]

        self.deallocate_node(rchild)

        while ipos < node.num-1:
            node.keys[ipos] = node.keys[ipos+1]
            node.docs[ipos] = node.docs[ipos+1]
            node.pnodes[ipos+1] = node.pnodes[ipos+2]
            ipos += 1
        node.num -= 1

        self.save_node(node)
        self.save_node(lchild)

    def pop(self, node=None, autoshrink=True):
        """
            弹出以 node 为起点的树中最后一个键值
        """

        if node is None:
            node = self.root

        if node.num == 0:
            return None

        if node.isleaf is True:
            key = node.keys[node.num-1]
            doc = node.docs[node.num-1]
            self.remove_key(node, key)
            if autoshrink is True:
                self.shrink()
            return key, doc

        while True:
            ipos = self.guarantee(node, node.num)
            child = self.load_node(node, ipos)
            if child.isleaf is True:
                break
            node = child

        child = self.load_node(node, node.num)
        key = child.keys[child.num-1]
        doc = child.docs[child.num-1]
        self.remove_key(node, key)
        if autoshrink is True:
            self.shrink()
        return key, doc

    def shift(self, node=None, autoshrink=True):
        """
            弹出以 node 为起点的树中第一个键值
        """

        if node is None:
            node = self.root

        if node.num == 0:
            return None

        if node.isleaf is True:
            key = node.keys[0]
            doc = node.docs[0]
            self.remove_key(node, key)
            if autoshrink is True:
                self.shrink()
            return key, doc

        while True:
            self.guarantee(node, 0)
            child = self.load_node(node, 0)
            if child.isleaf is True:
                break
            node = child

        child = self.load_node(node, 0)
        key = child.keys[0]
        doc = child.docs[0]
        self.remove_key(node, key)
        if autoshrink is True:
            self.shrink()
        return key, doc

    def shrink(self):
        if self.root.num == 0 and self.root.pnodes[0] is not None:
            old_root = self.root
            self.root = self.load_node(old_root, 0)
            self.deallocate_node(old_root)

    def guarantee(self, node, ipos):
        """
            确保 node.pnode[ipos] 拥有至少 t 个关键词
        """

        # Condition: 3
        child = self.load_node(node, ipos)
        if child.num >= self.degree:
            return ipos

        # Condition: 3a
        # 如果 ipos = 0，则 child 没有左兄弟
        if ipos > 0:
            lbrother = self.load_node(node, ipos-1)
            if lbrother.num >= self.degree:
                child.pnodes[child.num+1] = child.pnodes[child.num]
                icpos = child.num-1
                while icpos >= 0:
                    child.keys[icpos+1] = child.keys[icpos]
                    child.docs[icpos+1] = child.docs[icpos]
                    child.pnodes[icpos+1] = child.pnodes[icpos]
                    icpos -= 1
                child.keys[0] = node.keys[ipos-1]
                child.docs[0] = node.docs[ipos-1]
                child.pnodes[0] = lbrother.pnodes[lbrother.num]
                child.num += 1
                
                node.keys[ipos-1] = lbrother.keys[lbrother.num-1]
                node.docs[ipos-1] = lbrother.docs[lbrother.num-1]
                lbrother.num -= 1

                self.save_node(node)
                self.save_node(child)
                self.save_node(lbrother)
                return ipos

        # 如果 ipos = node.num， 则 child 没有右兄弟
        if ipos < node.num:
            rbrother = self.load_node(node, ipos+1)
            if rbrother.num >= self.degree:
                child.keys[child.num] = node.keys[ipos]
                child.docs[child.num] = node.docs[ipos]
                child.pnodes[child.num+1] = rbrother.pnodes[0]
                child.num += 1

                node.keys[ipos] = rbrother.keys[0]
                node.docs[ipos] = rbrother.docs[0]

                irpos = 0
                while irpos < rbrother.num-1:
                    rbrother.keys[irpos] = rbrother.keys[irpos+1]
                    rbrother.docs[irpos] = rbrother.docs[irpos+1]
                    rbrother.pnodes[irpos] = rbrother.pnodes[irpos+1]
                    irpos += 1
                rbrother.pnodes[irpos] = rbrother.pnodes[irpos+1]
                rbrother.num -= 1

                self.save_node(node)
                self.save_node(child)
                self.save_node(rbrother)
                return ipos

        # Condition: 3b
        # 如果指针指向最后一个位置(ipos = node.num)
        #   不存在 node.keys[ipos] 关键词
        #   结点 node.pnodes[ipos] 是 node.keys[ipos-1] 关键词的右孩子
        #   为了统一计算，将 ipos 左移一个位置，使得右孩子下标统一为 ipos+1
        if ipos == node.num:
            ipos -= 1
        self.merge(node, ipos)
        return ipos

    def remove_key(self, node, key):

        # 获取关键词所在的孩子结点位置
        # node.pnodes[ipos] 指向 目标孩子节点
        #   如果 ipos < node.num
        #       则 目标孩子 是 node.keys[ipos] 关键词的左孩子
        #   如果 ipos = node.num
        #       则 目标孩子 是 node.keys[ipos-1] 关键词的右孩子
        #
        # 如果判断 key 是否在 node.keys 中
        #   如果 ipos = 0
        #       则说明 key 不在 node.keys 中
        #   如果 ipos > 0
        #       则应该通过 key == node.keys[ipos-1] 判断是否包含
        ipos = node.num-1
        while ipos >= 0 and key < node.keys[ipos]:
            ipos -= 1
        ipos += 1

        if ipos > 0 and key == node.keys[ipos-1]:

            # 此时 node.keys[ipos] 为匹配的关键词
            ipos = ipos-1
            if node.isleaf is True:
                # Condition: 1
                while ipos < node.num-1:
                    node.keys[ipos] = node.keys[ipos+1]
                    node.docs[ipos] = node.docs[ipos+1]
                    ipos += 1
                node.num -= 1
                self.save_node(node)
                return 0
            else:
                # Condition: 2
                lchild = self.load_node(node, ipos)
                if lchild.num >= self.degree:
                    # Condition: 2a
                    node.keys[ipos], node.docs[ipos] = self.pop(lchild, False)
                    assert node.keys[ipos] is not None
                    self.save_node(node)
                    return 0

                # 因为已经匹配到了关键词，因此一定有右孩子
                rchild = self.load_node(node, ipos+1)
                if rchild.num >= self.degree:
                    # Condition: 2b
                    node.keys[ipos], node.docs[ipos] = self.shift(rchild, False)
                    assert node.keys[ipos] is not None
                    self.save_node(node)
                    return 0

                # Condition: 2c
                self.merge(node, ipos)
                return self.remove_key(self.load_node(node, ipos), key)
        else:
            if node.isleaf is True:
                # 没有找到要删除的节点
                return -1
            else:
                # Condition: 3
                ipos = self.guarantee(node, ipos)
                return self.remove_key(self.load_node(node, ipos), key)

    def remove(self, key):
        res = self.remove_key(self.root, key)
        self.shrink()
        return res

    def traverse(self, callback, node=None):
        if node is None:
            node = self.root

        callback(node)
        if node.isleaf is False:
            for ipos in xrange(node.num+1):
                self.traverse(callback, self.load_node(node, ipos))

    def print_node(self, node, strings, depth=0):
        if node is None:
            return 

        strings.append(">"*depth + str(node))
        if node.isleaf is False:
            strings.append("")
            for ipos in xrange(node.num+1):
                self.print_node(self.load_node(node, ipos), strings, depth+1)
            strings.append("")

    def __str__(self):
        strings = ["*****************************"]
        self.print_node(self.root, strings)
        return "\n".join(strings).strip() + "\n*****************************\n"


class MemNode(BNode):
    """内存级 B树 的点的结构"""
    def __init__(self, degree):
        super(MemNode, self).__init__(degree)
    
    def pointer(self):
        return self


class MemBTree(BTree):
    """
        内存级 B树
        仅用作实验，实际工程应用推荐使用 Dict
    """
    def __init__(self, degree):
        super(MemBTree, self).__init__(degree)

    def allocate_node(self):
        return MemNode(self.degree)

    def deallocate_node(self, node):
        return None

    def save_node(self, node):
        return None

    def load_node(self, node, ipos):
        return node.pnodes[ipos]

    def insert_value(self, node, ipos, doc):
        node.docs[ipos] = [doc]
        return 0

    def update_value(self, node, ipos, doc):
        node.docs[ipos].append(doc)
        return 1


class DiskNode(BNode):
    """
        磁盘级 B树 的点的结构
        一个节点的大小应该正好是硬盘的一页
    """
    def __init__(self, degree):
        super(DiskNode, self).__init__(degree)
        self.meta = None

    def pointer(self):
        return self.meta


class DiskBTree(BTree):
    """
        磁盘级 B树
    """
    def __init__(self, degree, folder):
        self.fs = FS(folder)
        super(DiskBTree, self).__init__(degree)

    def allocate_node(self):
        node = DiskNode(self.degree)
        node.meta = self.fs.generate_name()
        return node

    def deallocate_node(self, node):
        self.fs.remove(node.meta)
        return None

    def save_node(self, node):
        self.fs.save(pickle.dumps(node), node.meta)
        return None

    def load_node(self, node, ipos):
        return pickle.loads(self.fs.load(node.pnodes[ipos]))

    def insert_value(self, node, ipos, doc):
        node.docs[ipos] = [doc]
        self.save_node(node)
        return 0

    def update_value(self, node, ipos, doc):
        node.docs[ipos].append(doc)
        self.save_node(node)
        return 1
