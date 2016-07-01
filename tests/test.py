#!/usr/bin/env python

from runtime.models import Node, Exnode
from runtime.unisrt import UNISrt

rt = UNISrt()

print rt.exnodes.filter("name", "my_test_file")

exdata = {
    "mode": "file",
    "id": "blah",
    "name": "my_test_file",
    "size": 5555,
    "created": 1234,
    "modified": 5678,
    "owner": "ezra",
    "group": "ezra",
    "permission": "777",
    "parent": None,
    "extents": []
    }

ex = Exnode(data=exdata)
rt.insert(ex, sync=True)
