# -*- coding:utf-8 -*- 

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class Node(object):
    def __init__(self):
        super(Node, self).__init__()
        self.num = 0
        self.keys = []
        self.pnodes = []
        self.isleaf = True

class BNode(Node):
    def __init__(self, degree):
        super(BNode, self).__init__()
        self.degree = degree
        self.keys = [None for _ in xrange(degree*2-1)]
        self.pnodes = [None for _ in xrange(degree*2)]

    def __str__(self):
        return "Object:{0} num:{1} keys:{2}".format(
                    super(BNode, self).__str__(), self.num, self.keys) 

class BTree(object):
    """docstring for BTree"""
    def __init__(self, degree = 2):
        super(BTree, self).__init__()
        self.degree = degree
        self.threshold = degree*2-1
        self.root = BNode(self.degree)

    def search(self, key, node = None):
        
        if node is None:
            node = self.root

        ipos = 0
        while ipos < node.num and key > node.keys[ipos]:
            ipos += 1

        if ipos < node.num and key == node.keys[ipos]:
            return node, ipos

        if node.isleaf is True:
            return None

        return self.search(key, node.pnodes[ipos])

    def split(self, parent, ipos, node):

        new_node = BNode(self.degree)
        new_node.isleaf = node.isleaf
        for i in xrange(0, self.degree-1):
            new_node.keys[i] = node.keys[i+self.degree]
        new_node.num = node.num = self.degree-1

        if node.isleaf is False:
            for i in xrange(0, self.degree):
                new_node.pnodes[i] = node.pnodes[i+self.degree]

        for i in xrange(parent.num-1, ipos-1, -1):
            # 此处不会越界，因为在 insert 中有保护
            parent.keys[i+1] = parent.keys[i]
        parent.keys[ipos] = node.keys[self.degree-1]
        parent.num += 1

        for i in xrange(parent.num-1, ipos, -1):
            parent.pnodes[i+1] = parent.pnodes[i]
        parent.pnodes[ipos+1] = new_node

    def insert_key(self, node, key):

        ipos = node.num-1
        if node.isleaf is True:

            while ipos >= 0 and key < node.keys[ipos]:
                # 此处不会越界，因为在 insert 中有保护
                node.keys[ipos+1] = node.keys[ipos]
                ipos -= 1

            node.keys[ipos+1] = key
            node.num += 1
            return None

        # insert to non-leaf node, search child
        while ipos >= 0 and key < node.keys[ipos]:
            ipos -= 1

        ipos += 1
        child = node.pnodes[ipos]
        if child.num == self.threshold:
            self.split(node, ipos, child)
            if key > node.keys[ipos]:
                # 被插入的节点为新分裂出来的点
                ipos += 1
        self.insert_key(node.pnodes[ipos], key)

    def insert(self, key):

        if self.root.num != self.threshold:
            return self.insert_key(self.root, key)

        old_root = self.root
        new_root = BNode(self.degree)
        new_root.isleaf = False
        new_root.pnodes[0] = old_root

        self.root = new_root
        self.split(new_root, 0, old_root)
        self.insert_key(new_root, key)

    def merge(self, node, ipos):
        """
            将一个key左右两个兄弟合并
            ipos 是 node.keys 中关键词的位置
            ipos 也是 node.pnodes 中 关键词 左孩子的位置
        """

        lchild = node.pnodes[ipos]
        lchild.keys[lchild.num] = node.keys[ipos]
        lchild.num += 1

        rchild = node.pnodes[ipos+1]
        irpos = 0
        while irpos < rchild.num:
            lchild.keys[lchild.num+irpos] = rchild.keys[irpos]
            lchild.pnodes[lchild.num+irpos] = rchild.pnodes[irpos]
            irpos += 1
        lchild.num += rchild.num
        lchild.pnodes[lchild.num] = rchild.pnodes[rchild.num]

        # Free rchild

        while ipos < node.num-1:
            node.keys[ipos] = node.keys[ipos+1]
            node.pnodes[ipos+1] = node.pnodes[ipos+2]
            ipos += 1
        node.num -= 1

    def pop(self, node=None):
        """
            弹出以 node 为起点的树中最后一个键值
        """

        if node is None:
            node = self.root

        if node.num == 0:
            return None

        if node.isleaf is True:
            key = node.keys[node.num-1]
            self.remove_key(node, key)
            self.shrink()
            return key

        while True:
            ipos = self.guarantee(node, node.num)
            if node.pnodes[ipos].isleaf is True:
                break
            node = node.pnodes[ipos]

        child = node.pnodes[node.num]
        key = child.keys[child.num-1]
        self.remove_key(node, key)
        self.shrink()
        return key

    def shift(self, node=None):
        """
            弹出以 node 为起点的树中第一个键值
        """

        if node is None:
            node = self.root

        if node.num == 0:
            return None

        if node.isleaf is True:
            key = node.keys[0]
            self.remove_key(node, key)
            self.shrink()
            return key

        while True:
            self.guarantee(node, 0)
            if node.pnodes[0].isleaf is True:
                break
            node = node.pnodes[0]

        key = node.pnodes[0].keys[0]
        self.remove_key(node, key)
        self.shrink()
        return key

    def shrink(self):
        if self.root.num == 0 and self.root.pnodes[0] is not None:
            # Free root
            self.root = self.root.pnodes[0]

    def guarantee(self, node, ipos):
        """
            确保 node.pnode[ipos] 拥有至少 t 个关键词
        """

        # Condition: 3
        child = node.pnodes[ipos]
        if child.num >= self.degree:
            return ipos

        # Condition: 3a
        # 如果 ipos = 0，则 child 没有左兄弟
        if ipos > 0 and node.pnodes[ipos-1].num >= self.degree:
            lbrother = node.pnodes[ipos-1]
            child.pnodes[child.num+1] = child.pnodes[child.num]
            icpos = child.num-1
            while icpos >= 0:
                child.keys[icpos+1] = child.keys[icpos]
                child.pnodes[icpos+1] = child.pnodes[icpos]
                icpos -= 1
            child.keys[0] = node.keys[ipos-1]
            child.pnodes[0] = lbrother.pnodes[lbrother.num]
            child.num += 1
            
            node.keys[ipos-1] = lbrother.keys[lbrother.num-1]
            lbrother.num -= 1
            return ipos

        # 如果 ipos = node.num， 则 child 没有右兄弟
        if ipos < node.num and node.pnodes[ipos+1].num >= self.degree:
            rbrother = node.pnodes[ipos+1]
            child.keys[child.num] = node.keys[ipos]
            child.pnodes[child.num+1] = rbrother.pnodes[0]
            child.num += 1

            node.keys[ipos] = rbrother.keys[0]

            irpos = 0
            while irpos < rbrother.num-1:
                rbrother.keys[irpos] = rbrother.keys[irpos+1]
                rbrother.pnodes[irpos] = rbrother.pnodes[irpos+1]
                irpos += 1
            rbrother.pnodes[irpos] = rbrother.pnodes[irpos+1]
            rbrother.num -= 1
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
        #   如果 ipos < node.num，则 目标孩子 是 node.keys[ipos] 关键词的左孩子
        #   如果 ipos = node.num，则 目标孩子 是 node.keys[ipos-1] 关键词的右孩子
        #
        # 如果判断 key 是否在 node.keys 中
        #   如果 ipos = 0，则说明 key 不在 node.keys 中
        #   如果 ipos > 0，则应该通过 key == node.keys[ipos-1] 判断是否包含
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
                    ipos += 1
                node.num -= 1
                return 0
            else:
                # Condition: 2
                lchild = node.pnodes[ipos]
                if lchild.num >= self.degree:
                    # Condition: 2a
                    node.keys[ipos] = self.pop(lchild)
                    assert node.keys[ipos] is not None
                    return 0

                # 因为已经匹配到了关键词，因此一定有右孩子
                rchild = node.pnodes[ipos+1]
                if rchild.num >= self.degree:
                    # Condition: 2b
                    node.keys[ipos] = self.shift(rchild)
                    assert node.keys[ipos] is not None
                    return 0

                # Condition: 2c
                self.merge(node, ipos)
                return self.remove_key(node.pnodes[ipos], key)
        else:
            if node.isleaf is True:
                # 没有找到要删除的节点
                return -1
            else:
                # Condition: 3
                ipos = self.guarantee(node, ipos)
                return self.remove_key(node.pnodes[ipos], key)

    def remove(self, key):
        self.remove_key(self.root, key)
        self.shrink()

    def print_node(self, node, strings, depth=0):
        if node is None:
            return 

        strings.append(">"*depth + str(node.keys[:node.num])+" "+str(node.num))
        if node.isleaf is False:
            strings.append("")
            for ipos in xrange(node.num+1):
                self.print_node(node.pnodes[ipos], strings, depth+1)
            strings.append("")

    def __str__(self):
        strings = []
        self.print_node(self.root, strings)
        return "\n".join(strings)
