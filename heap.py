# -*- coding:utf-8 -*- 

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class Heap(object):
    """大顶堆"""
    def __init__(self, array=None, key=lambda x: x, cmp=cmp, reverse=False):
        super(Heap, self).__init__()

        if reverse is False:
            self.cmp = lambda x,y: cmp(key(x), key(y))
        else:
            self.cmp = lambda x,y: -cmp(key(x), key(y))

        self.heap = array or []
        self._init_heap()

    def add(self, e):
        self.heap.append(e)

        ipos = len(self.heap)-1
        while ipos > 0:
            iparent = int((ipos-1)/2)
            if self.cmp(self.heap[ipos], self.heap[iparent]) > 0:
                self.heap[iparent],self.heap[ipos] = self.heap[ipos],self.heap[iparent]
            ipos = iparent

    def pop(self, ipos=0):

        length = len(self.heap)
        if ipos > length:
            raise Exception("Heap has no position {0}, \
                             max positon is {1}", ipos, length-1)

        if length == 1:
            return self.heap.pop()

        element = self.heap[ipos]
        self.heap[ipos] = self.heap.pop()

        self._heap_down(ipos)
        return element
        
    def _heap_down(self, ipos):

        ileft = 2*ipos+1
        iright = 2*ipos+2
        n_size = len(self.heap)
        while ileft < n_size:
            if iright < n_size:
                if self.cmp(self.heap[ileft], self.heap[iright]) > 0:
                    if self.cmp(self.heap[ileft], self.heap[ipos]) > 0:
                        self.heap[ipos],self.heap[ileft] = self.heap[ileft],self.heap[ipos]
                elif self.cmp(self.heap[iright], self.heap[ipos]) > 0:
                    self.heap[ipos],self.heap[iright] = self.heap[iright],self.heap[ipos]
            elif self.cmp(self.heap[ileft], self.heap[ipos]) > 0 :
                self.heap[ipos],self.heap[ileft] = self.heap[ileft],self.heap[ipos]

            ipos += 1
            ileft = 2*ipos+1
            iright = 2*ipos+2

    def _init_heap(self):
        for ipos in xrange(int(len(self.heap)/2)-1, -1, -1):
            self._heap_down(ipos)

    @property
    def head(self):
        if len(self.heap) > 0:
            return self.heap[0]
        return None

    def __len__(self):
        return len(self.heap)

def heap_sort(array, key=lambda x: x, cmp=cmp, reverse=False, num=None):

    length = len(array)
    if length == 0:
        return array

    last = length-1
    if num is None or num > last or num < 0:
        num = length
    else:
        reverse = not reverse

    heap = Heap(array, key, cmp, reverse)

    lst = heap.heap
    diff = last - num
    while last > diff:
        ipos = 0
        lst[ipos], lst[last] = lst[last], lst[ipos]

        ileft = 2*ipos+1
        iright = 2*ipos+2
        while ileft < last:
            if iright < last:
                if heap.cmp(lst[ileft], lst[iright]) > 0:
                    if heap.cmp(lst[ileft], lst[ipos]) > 0:
                        lst[ipos],lst[ileft] = lst[ileft],lst[ipos]
                elif heap.cmp(lst[iright], lst[ipos]) > 0:
                    lst[ipos],lst[iright] = lst[iright],lst[ipos]
            elif heap.cmp(lst[ileft], lst[ipos]) > 0 :
                lst[ipos],lst[ileft] = lst[ileft],lst[ipos]

            ipos += 1
            ileft = 2*ipos+1
            iright = 2*ipos+2

        last -= 1

    return lst[length-num:length][::-1]
