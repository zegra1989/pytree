# -*- coding:utf-8 -*- 

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


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

    def overlap_area(self, rect):
        area = 1.0
        for ipos in xrange(self.dimension):
            if self.max_dim[ipos] < rect.max_dim[ipos]:
                factor = self.max_dim[ipos] - rect.min_dim[ipos]
                if factor < 0:
                    return 0.0
            else:
                factor = rect.max_dim[ipos] - self.min_dim[ipos]
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
            raise Exception("R树推荐维度为 [2,6]")

        self.threshold = degree*2
        self.rects = [None for _ in xrange(self.threshold)]
        self.pnodes = [None for _ in xrange(self.threshold)]

    def pointer(self):
        raise NotImplementedError()


class DataNode(object):
    """docstring for DataNode"""

    def __init__(self, max_length=10):
        super(DataNode, self).__init__()

        self.data = None
        self.max_length = max_length
        base, mode = divmod(self.max_length, 2)
        if mode > 0:
            base += 1
        self.min_length = base

        self.num = 0


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

    def insert(self, rect, doc):
        if self.root.num != self.threshold:
            return self.insert_nonfull(self.root, rect, doc)

        
