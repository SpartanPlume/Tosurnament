"""Helper module for bitfields manipulation"""

class BitField(int):
    """Stores an int and converts it to a string corresponding to an enum"""
    to_string = lambda self, enum: " ".join([i for i, j in enum._asdict().items() if self & j])
