# -*- coding:utf-8 -*- 

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


class NameNode(object):
    def __init__(self, degree, optimize=3):
        super(NameNode, self).__init__()
        self.num = 0
        self.degree = degree
        self.threshold = degree*2
        self.keys = [None for _ in xrange(self.threshold)]
        self.pnodes = [None for _ in xrange(self.threshold)]

        self.isleaf = True

    def pointer(self):
        return self

    def __str__(self):
        return "num:{0} keys:{1}".format(
                    self.num, self.keys[:self.num]) 


class DataNode(object):
    """docstring for DataNode"""

    F_INCREASE = 0
    F_DECREASE = 1

    def __init__(self, max_length=10, optimize=3):
        super(DataNode, self).__init__()

        self.data = None
        self.max_length = max_length
        base, mode = divmod(self.max_length, 2)
        if mode > 0:
            base += 1
        self.min_length = base

        self.num = 0

        # 记录上一次插入的数据
        self.last_insert_pos = None
        # 连续递增标识
        self.is_increase = None
        # 记录同一方向连续插入的数量
        self.n_directions = 0
        # 当同方向连续插入到达 n_optimize 时才会启动 split 优化
        self.n_optimize = optimize

        self.prev = None
        self.next = None

    def link(self, prev_node=None, next_node=None):

        if prev_node is not None:
            tmp = self.prev
            self.prev = prev_node
            prev_node.prev = tmp

            prev_node.next = self
            if prev_node.prev is not None:
                prev_node.prev.next = prev_node

        if next_node is not None:
            tmp = self.next
            self.next = next_node
            next_node.next = tmp

            next_node.prev = self
            if next_node.next is not None:
                next_node.next.prev = next_node

    def insert(self, data, doc):
        raise NotImplementedError()

    def update(self, data, doc):
        raise NotImplementedError()

    def pop(self, num=1):
        raise NotImplementedError()

    def isfull(self):
        raise NotImplementedError()

    def isguarenteed(self):
        raise NotImplementedError()

    def split(self, mode=None):
        raise NotImplementedError()

    def merge(self, datanode):
        raise NotImplementedError()

    @property
    def low_key(self):
        return self._low_key


class BPlusTree(object):

    def __init__(self, degree):
        super(BPlusTree, self).__init__()
        self.degree = degree
        self.threshold = degree*2
        self.root = self.allocate_namenode()

    def allocate_namenode(self):
        raise NotImplementedError()

    def deallocate_namenode(self, node):
        raise NotImplementedError()

    def allocate_datanode(self):
        raise NotImplementedError()

    def deallocate_datanode(self, node):
        raise NotImplementedError()

    def save_docs(self, metanode):
        raise NotImplementedError()

    def load_docs(self, metanode, ipos):
        raise NotImplementedError()

    def remove(self, key):
        res = self.remove_key(self.root, key)
        self.shrink()
        return res

    def shrink(self):
        if self.root.num == 1 and self.root.isleaf is False:
            old_root = self.root
            self.root = old_root.pnodes[0]
            self.deallocate_namenode(old_root)

    def update(self, key, doc):
        docs = self.search(key)
        if docs is None:
            node, ipos = self.insert2(key, doc)

            return 0
        docs = self.load_docs(node, ipos)
        docs.update(key, doc)
        return 1

    def select(self, key):
        node = self.search(key)
        if node is None:
            return None
        return node

    def search(self, key, node=None):
        if node is None:
            node = self.root

        ipos = node.num-1
        while ipos >= 0 and key < node.keys[ipos]:
            ipos -= 1

        # 如果 ipos<0 则，没有找到对应的key
        if ipos < 0:
            return None

        if node.isleaf is True:
            return self.load_docs(node.pnodes[ipos])

        return self.search(key, node.pnodes[ipos])

    def split(self, parent, ipos, node):
        
        if parent.isleaf is False:
            new_node = self.allocate_namenode()
            new_node.isleaf = node.isleaf

            for i in xrange(0, self.degree):
                new_node.keys[i] = node.keys[i+self.degree]
                new_node.pnodes[i] = node.pnodes[i+self.degree]
            new_node.num = node.num = self.degree

            for i in xrange(parent.num-1, ipos-1, -1):
                parent.keys[i+1] = parent.keys[i]
                parent.pnodes[i+1] = parent.pnodes[i]
            parent.keys[ipos+1] = new_node.keys[0]
            parent.pnodes[ipos+1] = new_node.pointer()
            parent.num += 1
            return None

        for i in xrange(parent.num-1, ipos-1, -1):
            # 此处不会越界，因为在 insert 中有保护
            parent.keys[i+1] = parent.keys[i]
            parent.pnodes[i+1] = parent.pnodes[i]

        # 优化 split 算法
        if node.n_directions > node.n_optimize:
            # 避开 MySQL Bug #67718
            if node.is_increase is True:
                # 连续递增插入
                new_node = node.split(mode=DataNode.F_INCREASE)
                ipos += 1
                node.link(next_node=new_node)
            else:
                # 连续递减插入
                new_node = node.split(mode=DataNode.F_DECREASE)
                parent.keys[ipos+1] = node.low_key
                node.link(prev_node=new_node)
        else:
            # 基础 split 算法
            new_node = node.split()
            ipos += 1
            node.link(next_node=new_node)

        parent.keys[ipos] = new_node.low_key
        parent.pnodes[ipos] = new_node
        parent.num += 1
        return None

    def insert_nonfull(self, node, key, doc):
        ipos = node.num-1
        while ipos >= 0 and key < node.keys[ipos]:
            ipos -= 1

        # 如果 ipos < 0，则说明要插入点小于当前节点中最小关键词
        if ipos < 0:
            node.keys[0] = key
            ipos = 0

        if node.isleaf is True:
            datanode = node.pnodes[ipos]
            if datanode is None:
                datanode = self.allocate_datanode()
                node.keys[ipos] = key
                node.pnodes[ipos] = datanode
                node.num += 1
                # 此处不用连接 DataNode 的链表，因为此处仅在初始化时运行一次

            if datanode.isfull() is True:
                if datanode.is_increase is True and datanode.last_insert_pos > key:
                    datanode.is_increase = False
                    datanode.n_directions = 1
                elif datanode.is_increase is False and datanode.last_insert_pos < key:
                    datanode.is_increase = True
                    datanode.n_directions = 1
                self.split(node, ipos, datanode)
                if node.keys[ipos+1] < key:
                    ipos += 1

            datanode = node.pnodes[ipos]
            datanode.insert(key, doc)
            node.keys[ipos] = datanode.low_key
            return None

        child = node.pnodes[ipos]
        if child.num == self.threshold:
            self.split(node, ipos, child)
        return self.insert_nonfull(child, key, doc)

    def insert(self, key, doc):
        if self.root.num != self.threshold:
            return self.insert_nonfull(self.root, key, doc)

        old_root = self.root
        new_root = self.allocate_namenode()
        new_root.isleaf = False
        new_root.keys[0] = old_root.keys[0]
        new_root.pnodes[0] = old_root.pointer()
        new_root.num += 1

        self.root = new_root
        self.split(new_root, 0, old_root)
        return self.insert_nonfull(new_root, key, doc)

    def merge(self, node, ipos):
        """
            将当前节点 关键词 对应的孩子与其 左/右兄弟 合并
            ipos 是 node.keys 中关键词的位置
        """

        # 当前节点没有右兄弟
        if ipos == node.num-1:
            ipos -= 1

        child = node.pnodes[ipos]
        rchild = node.pnodes[ipos+1]

        if node.isleaf is True:
            child.merge(rchild)
            self.deallocate_datanode(rchild)
        else:
            irpos = 0
            while irpos < rchild.num:
                # TODO
                child.keys[child.num+irpos] = rchild.keys[irpos]
                child.pnodes[child.num+irpos] = rchild.pnodes[irpos]
                irpos += 1
            child.num += rchild.num
            self.deallocate_namenode(rchild)

        inpos = ipos+1
        while inpos < node.num-1:
            node.keys[inpos] = node.keys[inpos+1]
            node.pnodes[inpos] = node.pnodes[inpos+1]
            inpos += 1
        node.num -= 1

        return ipos

    def guarantee(self, node, ipos):
        """
            确保 node.pnode[ipos] 拥有至少 t 个关键词
        """

        child = node.pnodes[ipos]
        if child.num > self.degree:
            return ipos

        # 如果 ipos = 0，则 child 没有左兄弟
        if ipos > 0:
            lbrother = node.pnodes[ipos-1]
            if lbrother.num > self.degree:
                icpos = child.num
                while icpos > 0:
                    child.keys[icpos] = child.keys[icpos-1]
                    child.pnodes[icpos] = child.pnodes[icpos-1]
                    icpos -= 1
                child.keys[0] = lbrother.keys[lbrother.num-1]
                child.pnodes[0] = lbrother.pnodes[lbrother.num-1]
                child.num += 1

                node.keys[ipos] = child.keys[0]
                lbrother.num -= 1
                return ipos

        # 如果 ipos = node.num-1， 则 child 没有右兄弟
        if ipos < node.num-1:
            rbrother = node.pnodes[ipos+1]
            if rbrother.num > self.degree:
                child.keys[child.num] = rbrother.keys[0]
                child.pnodes[child.num] = rbrother.pnodes[0]
                child.num += 1

                irpos = 0
                while irpos < rbrother.num-1:
                    rbrother.keys[irpos] = rbrother.keys[irpos+1]
                    rbrother.pnodes[irpos] = rbrother.pnodes[irpos+1]
                    irpos += 1

                node.keys[ipos+1] = rbrother.keys[0]
                rbrother.num -= 1
                return ipos

        return self.merge(node, ipos)

    def remove_key(self, node, key):
        ipos = node.num-1
        while ipos >= 0 and key < node.keys[ipos]:
            ipos -= 1

        # 如果 ipos < 0，则说明没有找到要删除的节点
        if ipos < 0:
            return None

        if node.isleaf is False:
            icpos = self.guarantee(node, ipos)
            child = node.pnodes[icpos]
            self.remove_key(child, key)
            node.keys[icpos] = node.pnodes[icpos].keys[0]
            return 0

        datanode = node.pnodes[ipos]
        if datanode.isguarenteed() is True:
            datanode.remove(key)
            node.keys[ipos] = datanode.low_key
            return datanode.low_key

        if node.num == 1:
            datanode.remove(key)
            if datanode.num > 0:
                node.keys[ipos] = datanode.low_key
            else:
                node.num = 0
                node.pnodes[0] = None
                self.deallocate_datanode(datanode)
            return 0

        if ipos > 0:
            lbrother = node.pnodes[ipos-1]
            if lbrother.isguarenteed() is True:
                lkey, ldoc = lbrother.pop()
                datanode.insert(lkey, ldoc)
                node.keys[ipos] = lkey
                datanode.remove(key)
                node.keys[ipos] = datanode.low_key
                return datanode.low_key

        if ipos < node.num-1:
            rbrother = node.pnodes[ipos+1]
            if rbrother.isguarenteed() is True:
                rkey, rdoc = rbrother.shift()
                datanode.insert(rkey, rdoc)
                node.keys[ipos+1] = rbrother.low_key
                datanode.remove(key)
                node.keys[ipos] = datanode.low_key
                return datanode.low_key

        ipos = self.merge(node, ipos)
        datanode = node.pnodes[ipos]
        datanode.remove(key)
        node.keys[ipos] = datanode.low_key
        return datanode.low_key

    def traverse(self, callback, node=None):
        pass

    def print_node(self, node, string, depth=0):
        pass

    def __str__(self):
        strings = ["*****************************"]
        self.print_node(self.root, strings)
        return "\n".join(strings).strip() + "\n*****************************\n"


################################################

class MemDataNode(DataNode):
    """docstring for MemDataNode"""
    def __init__(self, max_length=4):
        super(MemDataNode, self).__init__(max_length)
        self.data = {}

    def insert(self, key, doc):
        if isinstance(doc, list,) is True and len(doc) == 1:
            doc = doc[0]

        self.data[key] = [doc]
        self._low_key = min(self.data.keys())

        if self.is_increase is True:
            if self.last_insert_pos < key:
                self.n_directions += 1
            else:
                self.is_increase = False
                self.n_directions = 1
        else:
            if self.last_insert_pos > key:
                self.n_directions += 1
            else:
                self.is_increase = True
                self.n_directions = 1
        
        self.last_insert_pos = key
        self.num += 1

    def update(self, key, doc):
        docs = self.data.get(key, None)
        if docs is not None:
            docs.append(doc)
        else:
            self.data[key] = [doc]
            self.num += 1
        self._low_key = min(self.data.keys())

    def remove(self, key):
        del self.data[key]
        self.num -= 1
        if len(self.data) > 0:
            self._low_key = min(self.data.keys())
        else:
            self._low_key = None

    def isfull(self):
        return self.num == self.max_length

    def isguarenteed(self):
        return self.num > self.min_length

    def pop(self):
        key = sorted(self.data)[-1]
        doc = self.data.pop(key)
        if len(self.data) == 0:
            self._low_key = None
        self.num -= 1
        return key, doc

    def shift(self):
        key = sorted(self.data)[0]
        doc = self.data.pop(key)
        if len(self.data) == 0:
            self._low_key = None
        else:
            self._low_key = min(self.data.keys())
        self.num -= 1
        return key, doc

    def split(self, mode=None):
        new_node = MemDataNode(self.max_length)

        if mode is DataNode.F_INCREASE:
            key, doc = self.pop()
            new_node.insert(key, doc)
            self.num -= 1
        elif mode is DataNode.F_DECREASE:
            key, doc = self.shift()
            new_node.insert(key, doc)
            self.num -= 1
        else:
            for key in sorted(self.data)[self.min_length:]:
                new_node.insert(key, self.data.pop(key))
                self.num -= 1

        return new_node

    def merge(self, datanode):
        self.data.update(datanode.data)
        self.num = len(self.data)

    def __str__(self):

        keys = sorted(self.data.keys())
        values = map(lambda x: self.data[x], keys)
        return "num:{0} keys:{1} docs:{2}, increase:{3}".format(
                    len(self.data), keys, values, self.n_directions) 


class MemBPlusTree(BPlusTree):
    """docstring for MemBPlusTree"""
    def __init__(self, degree):
        super(MemBPlusTree, self).__init__(degree)

    def allocate_namenode(self):
        return NameNode(self.degree)

    def deallocate_namenode(self, node):
        pass

    def allocate_datanode(self):
        return MemDataNode()

    def deallocate_datanode(self, node):
        pass

    def load_docs(self, datanode):
        return datanode

    def print_node(self, node, strings, depth=0):
        if node is None:
            return 

        strings.append(">"*depth + str(node))
        if node.isleaf is False:
            strings.append("")
            for ipos in xrange(node.num):
                self.print_node(node.pnodes[ipos], strings, depth+1)
            strings.append("")
        else:
            for ipos in xrange(node.num):
                strings.append(">"*(depth+1) + str(node.pnodes[ipos]))

    def __str__(self):
        strings = ["*****************************"]
        self.print_node(self.root, strings)
        return "\n".join(strings).strip() + "\n*****************************\n"



# import random

# def test(length):

#     tree = MemBPlusTree(4)  
#     seq = set()
#     while len(seq) != length:
#         seq.add(int(random.random()*1000))
#     seq = list(seq)

#     random.shuffle(seq)
#     for num in seq:
#         tree.insert(num, num)

#     archive = list(seq)
#     random.shuffle(seq)
#     search = list(seq)

#     for num in seq:
#         node = tree.search(num)
#         if node is None:
#             print "**************************"
#             print num
#             print archive
#             print search
#             print "**************************"
#             exit()
#         try:
#             tree.remove(num)
#         except Exception as e:
#             print "==========================="
#             print num
#             print archive
#             print search
#             print "==========================="
#             exit()

#         node = tree.search(num)
#         if node is not None and num in node.data:
#             print "+++++++++++++++++++++++++"
#             print num
#             print archive
#             print search
#             print "+++++++++++++++++++++++++"
#             exit()


# LOOP = 10000
# LENGTH = 100
# for length in xrange(1, LENGTH):
#     print "Testing...", length
#     for _ in xrange(LOOP):
#         test(length)


# 639
# [994, 788, 200, 657, 130, 84, 135, 104, 768, 787, 789, 354, 762, 531, 973, 673, 530, 890, 928, 965, 739, 3, 168, 91, 136, 176, 666, 596, 114, 639]
# [673, 91, 596, 890, 994, 973, 928, 354, 739, 168, 768, 3, 135, 176, 200, 104, 530, 762, 965, 136, 788, 639, 789, 114, 130, 531, 787, 657, 84, 666]
