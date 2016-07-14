from settings import SCHEMAS
from . import schema_objects as uso

"""
Here we may specialize each UNIS object for the runtime
Each runtime class is defined by keys in the SCHEMAS dict
and inherits from the underlying JSON schema objects
"""

def __str_name(self):
    return "<{0} {1}>".format(self.__class__.__name__,
                              self.name)

def __str_location(self):
    return "<{0} {1}>".format(self.__class__.__name__,
                              self.location)

def __repr(self):
    return self.__str__()

for key, value in SCHEMAS.items():
    parent = getattr(uso, key)
    cls = type(key, (parent, ), {})
    cls.__str__  = __str_name
    cls.__repr__ = __repr
    vars()[key] = cls

def __exnode_init(self, data=None):
    super(Exnode, self).__init__(data)
    if isinstance(self.extents, list):
        extents = []
        for e in self.extents:
            ext = Extent(e)
            extents.append(ext)
        if len(extents):
            self.extents = extents
    
vars()["Exnode"].__init__ = __exnode_init
vars()["Extent"].__str__ = __str_location
