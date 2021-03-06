from decimal import Decimal, ROUND_HALF_UP
import math

__all__ = ["functions", "Nothing", "NothingType"]


class Singleton(type):
    """Ensures that there is only ever one instance of a class"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class NothingType(metaclass=Singleton):
    """
    Similar to Python's `NoneType` but all mathematical operations on it simply return Nothing.
    Additionally, allows us to encode the principle behind `None` into our language.
    """

    def __lt__(self, other): return False
    def __gt__(self, other): return False
    def __eq__(self, other): return other is NothingType()
    def __ne__(self, other): return not (self == other)
    def __ge__(self, other): return self == other
    def __le__(self, other): return self == other
    def __bool__(self): return False
    def __repr__(self): return "Nothing"

    @classmethod
    def _class_init(cls):
        """
        Define all mathematical operations on NothingType to simply return the NothingType.
        E.g., Nothing + 3 is Nothing, round(Nothing) is Nothing etc.
        """
        magic_methods = ["add", "and", "ceil", "divmod", "float",
                         "floor", "floordiv", "gt", "int", "lt",
                         "lshift", "mod", "mul", "neg", "or", "pos",
                         "pow", "radd", "rdivmod", "rfloordiv", "rlshift",
                         "rmod", "rmul", "ror", "round", "rpow", "rrshift",
                         "rshift", "rsub", "rtruediv", "rxor", "str", "sub",
                         "truediv", "trunc", "xor"]

        for method in magic_methods:
            def fn(self, *unused): return self
            fn.__name__ = f"__{method}__"
            setattr(cls, fn.__name__, fn)


NothingType._class_init()
delattr(NothingType, "_class_init")
Nothing = NothingType()


def avg(*args):
    denominator = 0
    numerator = 0
    for arg in args:
        score, weight = arg if isinstance(arg, tuple) else (arg, 1)
        if score is not Nothing:
            denominator += weight
            numerator += score * weight
    return numerator / denominator if denominator else Nothing


# TODO
import random
def score(slug): return round(random.random(), 2)


def round(num, place=0):
    """
    Python's round rounds toward even numbers e.g. round(2.5) == 2 but round(3.5) == 4.
    This round function mimics the API of python's round but always round x.5 to x+1.
    """
    return Nothing if num is Nothing else \
        (float if place else int)(Decimal(num).quantize(
            Decimal(str(10 ** -place)), rounding=ROUND_HALF_UP))


functions = {fn.__name__: fn for fn in [
    math.ceil, math.floor, max, min, score, round, avg]}
functions.update({
    # We call the magic functions directly because Nothing implements them to return Nothing,
    # but int()/float()/str() proper throw a type error if the return is not of expected type
    "int": lambda x: x.__int__(),
    "float": lambda x: x.__float__(),
    "str": lambda x: x.__str__(),
})
