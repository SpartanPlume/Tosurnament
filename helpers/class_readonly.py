"""Helper module to put a class in readonly"""

from collections import namedtuple

def readonly(args):
    """Puts a class in readonly"""
    class Empty: pass
    defaults = vars(Empty).keys()
    keys, values = zip(*[(i, j) for i, j in vars(args).items() if i not in defaults])
    return namedtuple("Const", keys)(*values)
