# -*- coding:utf-8 -*- 

# 使用 UTF-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import os
import uuid

class FS(object):
    """docstring for FS"""
    def __init__(self, root_path=None, strategy=None):
        super(FS, self).__init__()
        self.root_path = os.path.abspath(root_path or ".")
        self.strategy = strategy if strategy is not None else [8,8,8,8]

    def generate_name(self):
        while True:
            ipos = 0
            shards = []
            seed = uuid.uuid4().get_hex()
            for gap in self.strategy:
                shards.append(seed[ipos:ipos+gap])
                ipos += gap
            path = os.path.join(self.root_path, *shards)
            if os.path.exists(path) is False:
                break
        return path

    def save(self, data, path=None):

        if path is None:
            path = self.generate_name()
        elif os.path.isabs(path) is False:
            path = os.path.join(self.root_path, path)

        folder, name = os.path.split(path)

        if os.path.exists(folder) is False:
            os.makedirs(folder)

        with open(path, "wb") as fileobj:
            fileobj.write(data)

        return os.path.relpath(path, self.root_path)

    def load(self, path):

        if os.path.isabs(path) is False:
            path = os.path.join(self.root_path, path)

        with open(path, "rb") as fileobj:
            return fileobj.read()
            
    def remove(self, path):

        if os.path.isabs(path) is False:
            path = os.path.join(self.root_path, path)

        os.remove(path)

        folder, name = os.path.split(path)
        _, _, files = os.walk(folder).next()
        if len(files) == 0:
            os.removedirs(folder)

