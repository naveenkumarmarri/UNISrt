#!/usr/bin/env python

from pprint import pprint
from runtime.models import Node, Exnode
from runtime.unisrt import UNISrt

rt = UNISrt()

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
    "extents": [
        {
            "$schema": "http://unis.crest.iu.edu/schema/exnode/4/extent#",
            "parent": {
                "href": "#/blah",
                "rel": "full"
            },
            "lifetimes": [
                {
                    "start": "2016-07-12 00:45:57",
                    "end": "2016-08-11 00:45:57"
                }
            ],
            "mapping": {
                "read": "ibp://dresci.incntre.iu.edu:6714/0#X1nNmGCHKhBFm0HN-9NRKauY8tZXSnYb/7187287695477547766/READ",
                "write": "ibp://dresci.incntre.iu.edu:6714/0#VkjlWPJvwvUQ7DiUJnuDyra6idUHO8EY/7187287695477547766/WRITE",
                "manage": "ibp://dresci.incntre.iu.edu:6714/0#iF2m8AAMcZ5vf3VWU4p5eR+bTvS-o-bs/7187287695477547766/MANAGE"
            },
            "location": "ibp://",
            "offset": 0,
            "size": 1022574
        }
    ]
}

test = Exnode()

ex = Exnode(data=exdata)

pprint (ex.as_dict())
print (type(ex.extents[0]))

rt.insert(ex, sync=True)
exs = rt.exnodes.filter("name", "my_test_file")
print (exs)
