# -*- coding:utf-8 -*- 

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from heap import Heap

class Rectangle(object):
    """docstring for Rectangle"""
    def __init__(self, dimension):
        super(Rectangle, self).__init__()
        self.dimension = dimension
        self.min_dim = [None for _ in xrange(dimension)]
        self.max_dim = [None for _ in xrange(dimension)]

    def resize(self, rects):
        """
            通过给定的 子节点Rectangle列表
            重新计算当前 Rectangle 的 MBR(Minimal Boundary Rect)
        """
        for ipos in xrange(self.dimension):
            self.min_dim[ipos] = min(map(lambda x: x.min_dim[ipos], rects))
            self.max_dim[ipos] = max(map(lambda x: x.max_dim[ipos], rects))

    def resize2(self, entry):
        """
            通过给定的 entry,
            重新计算当前 Rectangle 的 MBR(Minimal Boundary Rect)
            entry 代表一条数据的所有维度
        """
        for ipos in xrange(self.dimension):
            if entry[ipos] < self.min_dim[ipos]:
                self.min_dim[ipos] = entry[ipos]
            elif entry[ipos] > self.max_dim[ipos]:
                self.max_dim[ipos] = entry[ipos]

    def overlap_area(self, rect):
        area = 1.0
        for ipos in xrange(self.dimension):
            try:
                if self.max_dim[ipos] < rect.max_dim[ipos]:
                    factor = self.max_dim[ipos] - rect.min_dim[ipos]
                else:
                    factor = rect.max_dim[ipos] - self.min_dim[ipos]
            except TypeError as e:
                # 未完全初始化的 Rectangle
                return -1

            if factor < 0:
                return 0.0

            area *= factor
        return area

    def __contains__(self, rect):
        for ipos in xrange(self.dimension):
            if self.max_dim[ipos] < rect.min_dim[ipos]:
                return False
            if self.min_dim[ipos] > rect.max_dim[ipos]:
                return False
        return True

    def __str__(self):
        return "Min:{0}, Max:{1}".format(
                    self.min_dim, self.max_dim) 


class RNode(object):
    def __init__(self, degree, dimension):
        super(RNode, self).__init__()
        self.num = 0
        self.isleaf = True
        self.degree = degree
        self.dimension = dimension

        if dimension < 2:
            raise Exception("请使用 B/B+树 代替")
        if dimension > 6:
            print "WARNING:R树推荐维度为 [2,6]"

        self.mbr = Rectangle(self.dimension)
        self.threshold = degree*2
        self.rects = [None for _ in xrange(self.threshold)]
        self.pnodes = [None for _ in xrange(self.threshold)]

    def adjust(self):
        self.mbr = Rectangle(self.dimension)
        self.mbr.resize(self.rects[:self.num])

    def involve(self, entry):
        self.mbr.resize2(entry)

    def pointer(self):
        return self


class DataNode(object):
    """docstring for DataNode"""

    def __init__(self, max_length=10):
        super(DataNode, self).__init__()

        self.num = 0
        self.data = None
        self.max_length = max_length
        base, mode = divmod(self.max_length, 2)
        if mode > 0:
            base += 1
        self.min_length = base

    def mbr(self):
        raise NotImplementedError()


class RTree(object):
    """docstring for RTree"""
    def __init__(self, degree, dimension):
        super(RTree, self).__init__()
        self.degree = degree
        self.dimension = dimension
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

    def search(self, rect, node=None):
        if node is None:
            node = self.root

        indexes = []
        ipos = node.num-1
        while ipos >= 0:
            if rect in node.rects[ipos]:
                indexes.append(ipos)

        if len(indexes) == 0:
            return []

        if node.isleaf is True:
            return map(lambda x: self.load_docs(node.pnodes[x]), indexes)

        results = []
        for ipos in indexes:
            results.extend(self.search(rect, node.pnodes[ipos]))

        return results

    def split(self, parent, ipos, node):
        """
            由于 R树 中节点内部是无序的，为了减少移动数据的开销
            分裂后的两个节点一个放在分裂前节点的位置，一个放在末尾

            目前分裂的简单算法：
                直接选取第一个点当作旧节点的核心rect
                计算旧核心rect与其他rect的重合度
                选取重合度最低的一个rect作为新节点的核心rect
                计算新核心rect与其他rect的重合度
                对比每个非核心rect与两个核心的重合度
                选出与新核心重合度更高的 degree-1 个节点组成新节点
        """

        if parent.isleaf is False:
            new_node = self.allocate_namenode()
            new_node.isleaf = node.isleaf

            ancor = node.rects[0]
            heap = Heap(node.pnodes, reverse=True,
                        key=lambda x: ancor.overlap_area(x.mbr))

            ipos = 0
            while ipos < node.degree:
                new_node.pnodes[ipos] = heap.pop()
                new_node.rects[ipos] = new_node.pnodes[ipos].mbr
                ipos += 1
            new_node.num = node.degree
            new_node.adjust()

            ipos = 0
            length = len(heap)
            while ipos < length:
                node.pnodes[ipos] = heap.heap[ipos]
                node.pnodes[ipos].adjust()
                node.rects[ipos] = heap.heap[ipos].mbr
                ipos += 1
            node.num = length
            node.adjust()
                
            parent.pnodes[parent.num-1] = new_node.pointer()
            parent.rects[parent.num-1] = new_node.mbr
            parent.num += 1
            return None

        new_node = node.split()
        parent.pnodes[parent.num-1] = new_node.pointer()
        parent.rects[parent.num-1] = new_node.mbr
        parent.num += 1
        return None

    def insert(self, entry, doc):
        """
            entry 是长度为 self.dimension 的数组
            entry 中每一个维度都需要是数值型
        """
        if self.root.num != self.threshold:
            return self.insert_nonfull(self.root, entry, doc)

        old_root = self.root
        new_root = self.allocate_namenode()
        new_root.isleaf = False
        new_root.pnodes[0] = old_root.pointer()
        new_root.rects[0] = old_root.mbr
        new_root.num += 1

        self.root = new_root
        self.split(new_root, 0, old_root)
        return self.insert_nonfull(new_root, entry, doc)

    def insert_nonfull(self, node, entry, doc):

        #TODO
        pass


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
        if node.keys[ipos+1] is not None and node.keys[ipos+1] < key:
            child = node.pnodes[ipos+1]
        return self.insert_nonfull(child, key, doc)

