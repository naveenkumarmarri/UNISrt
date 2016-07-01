import schema_objects as uso
import inspect
import uuid

"""
Here we may specialize each UNIS object for the runtime
"""

class Topology(uso.Topology):
    pass

class Domain(uso.Domain):
    pass

class Network(uso.Network):
    pass

class Node(uso.Node):
    pass

class Port(uso.Port):
    pass

class Link(uso.Link):
    pass

class Path(uso.Path):
    pass

class Service(uso.Service):
    pass

class Measurement(uso.Measurement):
    pass

class Datum(uso.Datum):
    pass

class Data(uso.Data):
    pass

class Metadata(uso.Metadata):
    pass

class Exnode(uso.Exnode):
    def __str__(self):
        return "<class Exnode {exp}>".format(exp=self.name)

    def __repr__(self):
        return self.__str__()

class Extent(uso.Extent):
    def __str__(self):
        return "<class Extent {exp}>".format(exp=self.location)

    def __repr__(self):
        return self.__str__()

class Manifest(uso.Manifest):
    pass
