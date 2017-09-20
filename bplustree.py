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

    def split(self, mode=None):
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
                self.split(node, ipos, datanode)
                if node.keys[ipos+1] < key:
                    ipos += 1

            node.pnodes[ipos].insert(key, doc)
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

        irpos = 0
        while irpos < rchild.num:
            child.keys[child.num+irpos] = rchild.keys[irpos]
            child.pnodes[child.num+irpos] = rchild.pnodes[irpos]
            irpos += 1
        child.num += rchild.num

        self.deallocate_namenode(rchild)

        inpos = ipos
        while inpos < node.num-1:
            node.keys[inpos] = node.keys[inpos+1]
            node.pnodes[inpos] = node.pnodes[inpos+1]
            inpos += 1

        node.num += 1
        return inpos

    def pop(self, node=None, autoshrink=True):
        pass

    def shift(self, node=None, autoshrink=True):
        pass

    def shrink(self):
        pass

    def guarantee(self, node, ipos):
        """
            确保 node.pnode[ipos] 拥有至少 t 个关键词
        """

        child = node.pnodes[ipos]
        if child.num >= self.degree:
            return ipos

        # 如果 ipos = 0，则 child 没有左兄弟
        if ipos > 0:
            lbrother = node.pnodes[ipos-1]
            if lbrother.num >= self.degree:
                icpos = child.num
                while icpos > 0:
                    child.keys[icpos] = child.keys[icpos-1]
                    child.pnodes[icpos] = child.pnodes[icpos-1]
                    icpos -= 1
                child.keys[0] = lbrother.keys[lbrother.num-1]
                child.pnodes[0] = lbrother.keys[lbrother.num-1]
                child.num += 1

                node.keys[ipos] = child.keys[0]
                lbrother.num -= 1
                return ipos

        # 如果 ipos = node.num-1， 则 child 没有右兄弟
        if ipos < node.num-1:
            rbrother = node.pnodes[ipos+1]
            if rbrother.num >= self.degree:
                child.keys[child.num] = rbrother.keys[0]
                child.pnodes[child.num] = rbrother.pnodes[0]
                child += 1

                irpos = 0
                while irpos < rbrother.num-1:
                    rbrother.keys[irpos] = rbrother.keys[irpos+1]
                    rbrother.pnodes[irpos] = rbrother.keys[irpos+1]
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
            return -1

        while node.isleaf is False:
            node = node.pnodes[self.guarantee(node, ipos)]
            ipos = node.num-1
            while ipos >= 0 and key < node.keys[ipos]:
                ipos -= 1

        # TODO
        datanode = node.pnodes[ipos]
        if datanode.num > datanode.min_length:
            datanode.remove(key)
            node.keys[ipos] = datanode.low_key
            return 0

        if ipos > 0:
            lbrother = node.pnodes[ipos-1]
            if lbrother.num > lbrother.min_length:
                lkey, ldoc = lbrother.pop()
                datanode.insert(lkey, ldoc)
                node.keys[ipos] = lkey
                datanode.remove(key)
                node.keys[ipos] = datanode.low_key
                return 0

        if ipos < node.num-1:
            rbrother = node.pnodes[ipos+1]
            if rbrother.num > rbrother.min_length:
                rkey, rdoc = rbrother.shift()
                datanode.insert(rkey, rdoc)
                node.keys[ipos+1] = rbrother.low_key
                datanode.remove(key)
                node.keys[ipos] = datanode.low_key
                return 0

        ipos = self.merge(node, ipos)
        datanode = node.pnodes[ipos]
        datanode.remove(key)
        node.keys[ipos] = datanode.low_key
        return 0

    def remove(self, key):
        pass

    def traverse(self, callback, node=None):
        pass

    def print_node(self, node, string, depth=0):
        pass

    def __str__(self):
        strings = ["*****************************"]
        self.print_node(self.root, strings)
        return "\n".join(strings).strip() + "\n*****************************\n"


################################################

class TestDataNode(DataNode):
    """docstring for TestDataNode"""
    def __init__(self, max_length=4):
        super(TestDataNode, self).__init__(max_length)
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

    def update(self, key, doc):
        docs = self.data.get(key, [])
        docs.append(doc)
        self._low_key = min(self.data.keys())

    def isfull(self):
        return len(self.data) == self.max_length

    def split(self, mode=None):
        new_node = TestDataNode(self.max_length)

        if mode is DataNode.F_INCREASE:
            key = sorted(self.data)[-1]
            new_node.insert(key, self.data.pop(key))
        elif mode is DataNode.F_DECREASE:
            key = sorted(self.data)[0]
            new_node.insert(key, self.data.pop(key))
            self._low_key = min(self.data.keys())
        else:
            for key in sorted(self.data)[self.min_length:]:
                new_node.insert(key, self.data.pop(key))

        return new_node

    def __str__(self):
        return "num:{0} keys:{1} docs:{2}, increase:{3}".format(
                    len(self.data), self.data.keys(), self.data.values(), self.n_directions) 


class TestBPlusTree(BPlusTree):
    """docstring for TestBPlusTree"""
    def __init__(self, degree):
        super(TestBPlusTree, self).__init__(degree)

    def allocate_namenode(self):
        return NameNode(self.degree)

    def deallocate_namenode(self, node):
        pass

    def allocate_datanode(self):
        return TestDataNode()

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


# tree = TestBPlusTree(2)

# tree.insert(100, 100)
# tree.insert(10, 10)
# tree.insert(50, 50)
# tree.insert(20, 20)
# tree.insert(120, 120)
# tree.insert(70, 70)
# tree.insert(90, 90)
# tree.insert(80, 80)
# tree.insert(60, 60)
# tree.insert(65, 65)
# tree.insert(55, 55)
# tree.insert(54, 54)
# tree.insert(53, 53)
# tree.insert(52, 52)
# tree.insert(51, 51)

# # import pdb
# # pdb.set_trace()

# print tree
# datanode = tree.root.pnodes[0].pnodes[0]

# while datanode is not None:
#     print datanode
#     print "prev->", datanode.prev
#     print "next->", datanode.next
#     print 
#     datanode = datanode.next
    
# # datanode = tree.root.pnodes[0].pnodes[0]
# # print datanode
# # print datanode.prev
# # print datanode.next
# # print datanode.next.next.next


tree = TestBPlusTree(2)
# tree.insert(0, 0)
tree.insert(100, 100)
tree.insert(90, 90)
tree.insert(80, 80)
tree.insert(70, 70)
tree.insert(60, 60)
tree.insert(65, 65)

# import pdb
# pdb.set_trace()

tree.insert(50, 50)
tree.insert(40, 40)


print tree