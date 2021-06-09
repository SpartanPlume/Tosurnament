import sys


class Cell:
    """Contains coordinates and a value."""

    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        super().__setattr__("value", str(value))
        self.value_type = type(value)
        self.x_merge_range = [x]
        self.y_merge_range = [y]
        self._updated = False

    def __setattr__(self, name, value):
        if name == "value":
            super().__setattr__("_updated", True)
            super().__setattr__("value_type", type(value))
            return super().__setattr__(name, str(value))
        return super().__setattr__(name, value)

    def set(self, new_value):
        self.value = new_value

    def get(self):
        if self.value_type == bool:
            if self.value == "True":
                return True
            else:
                return False
        try:
            return self.value_type(self.value)
        except Exception:
            return self.value

    def set_merge_range(self, x_merge_range, y_merge_range):
        """Sets the x_range and y_range of the merge containing this cell."""
        self.x_merge_range = x_merge_range
        self.y_merge_range = y_merge_range

    def has_value(self, value_to_compare, case_sensitive=False):
        """Checks if the cell contains a value. To use in case of multi values like: value1/value2."""
        cell_value = self.value
        value_to_compare = str(value_to_compare)
        if not case_sensitive:
            value_to_compare = value_to_compare.casefold()
            cell_value = cell_value.casefold()
        if cell_value == value_to_compare:
            return True
        values = cell_value.split("/")
        for value in values:
            if value.strip() == value_to_compare:
                return True
        return False

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "Cell(%i, %i, %s)" % (self.x, self.y, self.value)

    def __int__(self):
        return int(self.value)

    def __long__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __complex__(self):
        return complex(self.value)

    def __oct__(self):
        return oct(self.value)

    def __hex__(self):
        return hex(self.value)

    def __index__(self):
        return int(self.value)

    def __trunc__(self):
        return int(self.value)

    def __coerce__(self):
        return None

    def __hash__(self):
        return hash(self.value)

    def __nonzero__(self):
        if self.value_type == bool:
            if self.value == "True":
                return True
            else:
                return False
        return bool(self.value)

    def __iter__(self):
        return iter(self.value)

    def __reversed__(self):
        return reversed(self.value)

    def __getnewargs__(self):
        return (self.value[:],)

    def __eq__(self, other):
        if self.value_type == bool:
            bool_value = True if self.value == "True" else False
            return bool_value == other
        if isinstance(other, Cell):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Cell):
            return self.value < other.value
        return self.value < other

    def __le__(self, other):
        if isinstance(other, Cell):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other):
        if isinstance(other, Cell):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other):
        if isinstance(other, Cell):
            return self.value >= other.value
        return self.value >= other

    def __contains__(self, char):
        if isinstance(char, Cell):
            char = char.value
        return char in self.value

    def __len__(self):
        return len(str(self.value))

    def __getitem__(self, index):
        return self.value[index]

    def __add__(self, other):
        if isinstance(other, Cell):
            return self.value + other.value
        elif isinstance(other, str):
            return self.value + other
        return self.value + str(other)

    def __radd__(self, other):
        if isinstance(other, str):
            return other + self.value
        return str(other) + self.value

    def __mul__(self, n):
        return self.value * n

    __rmul__ = __mul__

    def __mod__(self, args):
        return self.value % args

    def __rmod__(self, template):
        return str(template) % self

    def capitalize(self):
        return self.value.capitalize()

    def casefold(self):
        return self.value.casefold()

    def center(self, width, *args):
        return self.value.center(width, *args)

    def count(self, sub, start=0, end=sys.maxsize):
        if isinstance(sub, Cell):
            sub = sub.value
        return self.value.count(sub, start, end)

    def removeprefix(self, prefix, /):
        if isinstance(prefix, Cell):
            prefix = prefix.value
        return self.value.removeprefix(prefix)

    def removesuffix(self, suffix, /):
        if isinstance(suffix, Cell):
            suffix = suffix.value
        return self.value.removesuffix(suffix)

    def encode(self, encoding="utf-8", errors="strict"):
        encoding = "utf-8" if encoding is None else encoding
        errors = "strict" if errors is None else errors
        return self.value.encode(encoding, errors)

    def endswith(self, suffix, start=0, end=sys.maxsize):
        return self.value.endswith(suffix, start, end)

    def expandtabs(self, tabsize=8):
        return self.value.expandtabs(tabsize)

    def find(self, sub, start=0, end=sys.maxsize):
        if isinstance(sub, Cell):
            sub = sub.value
        return self.value.find(sub, start, end)

    def format(self, /, *args, **kwds):
        return self.value.format(*args, **kwds)

    def format_map(self, mapping):
        return self.value.format_map(mapping)

    def index(self, sub, start=0, end=sys.maxsize):
        return self.value.index(sub, start, end)

    def isalpha(self):
        return self.value.isalpha()

    def isalnum(self):
        return self.value.isalnum()

    def isascii(self):
        return self.value.isascii()

    def isdecimal(self):
        return self.value.isdecimal()

    def isdigit(self):
        return self.value.isdigit()

    def isidentifier(self):
        return self.value.isidentifier()

    def islower(self):
        return self.value.islower()

    def isnumeric(self):
        return self.value.isnumeric()

    def isprintable(self):
        return self.value.isprintable()

    def isspace(self):
        return self.value.isspace()

    def istitle(self):
        return self.value.istitle()

    def isupper(self):
        return self.value.isupper()

    def join(self, seq):
        return self.value.join(seq)

    def ljust(self, width, *args):
        return self.value.ljust(width, *args)

    def lower(self):
        return self.value.lower()

    def lstrip(self, chars=None):
        return self.value.lstrip(chars)

    maketrans = str.maketrans

    def partition(self, sep):
        return self.value.partition(sep)

    def replace(self, old, new, maxsplit=-1):
        if isinstance(old, Cell):
            old = old.value
        if isinstance(new, Cell):
            new = new.value
        return self.value.replace(old, new, maxsplit)

    def rfind(self, sub, start=0, end=sys.maxsize):
        if isinstance(sub, Cell):
            sub = sub.value
        return self.value.rfind(sub, start, end)

    def rindex(self, sub, start=0, end=sys.maxsize):
        return self.value.rindex(sub, start, end)

    def rjust(self, width, *args):
        return self.value.rjust(width, *args)

    def rpartition(self, sep):
        return self.value.rpartition(sep)

    def rstrip(self, chars=None):
        return self.value.rstrip(chars)

    def split(self, sep=None, maxsplit=-1):
        return self.value.split(sep, maxsplit)

    def rsplit(self, sep=None, maxsplit=-1):
        return self.value.rsplit(sep, maxsplit)

    def splitlines(self, keepends=False):
        return self.value.splitlines(keepends)

    def startswith(self, prefix, start=0, end=sys.maxsize):
        return self.value.startswith(prefix, start, end)

    def strip(self, chars=None):
        return self.value.strip(chars)

    def swapcase(self):
        return self.value.swapcase()

    def title(self):
        return self.value.title()

    def translate(self, *args):
        return self.value.translate(*args)

    def upper(self):
        return self.value.upper()

    def zfill(self, width):
        return self.value.zfill(width)
