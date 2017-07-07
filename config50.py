#!/usr/bin/env python3
from itertools import islice

from arpeggio import RegExMatch, Optional, ZeroOrMore, OneOrMore, EOF, Kwd
from arpeggio import ParserPython, PTNodeVisitor, visit_parse_tree, ArpeggioError

from stdlib import Nothing, functions

WORD = r"[A-z][\w\-\.]*"

# Terminals
def comment():      return r"#", RegExMatch(r".*")
def number():       return RegExMatch(r"\d+\.\d*|\.\d+|\d+")
def identifier():   return RegExMatch(WORD)
def string():       return RegExMatch(r'"[^"]*"')
def nothing():      return "Nothing"

# Non-terminals
#TODO: Improve tuple grammar?
def tuple_():       return "(", assignment, ZeroOrMore(",", assignment), Optional(","), ")"
def arglist():      return assignment, ZeroOrMore(",", assignment)
def function():     return RegExMatch(WORD), "(", Optional(arglist), ")"
def atom():         return [nothing, string, function, number, identifier, tuple_]
def factor():       return Optional(["+", "-"]), [("(", assignment, ")"), atom]
def term():         return factor, ZeroOrMore(["*", "//", "/"], factor)
def arith():        return term, ZeroOrMore(["+", "-"], term)
def comparison():   return arith, ZeroOrMore(["<=", ">=", "==", "!=", "<", ">"], arith)
def assignment():   return Optional(RegExMatch(WORD) , "="), comparison
def config():       return ZeroOrMore(assignment), EOF


def windows(items, size, jump):
    """
    Creates iterator over windows of size `size` whose
    starting elements are `jump` away from each other in
    `items`.

    Ex: list(windows("abcdefg", 3, 2)) yields ["abc", "cde", "efg"]
    """

    for start in range(0, len(items), jump):
        yield next(zip(*([islice(items, start, None)] * size)))


class Config50Visitor(PTNodeVisitor):
    reserved_keywords = ["Nothing"]

    def __init__(self, functions, debug=False):
        super().__init__(debug=debug)
        # Dictionary of user-created variables
        self.symbols = {}
        # Dictionary mapping function names to builtin-functions
        self.functions = functions

    def visit_number(self, node, children):
        # Numbers get parsed as integers unless they have a "."
        return (float if "." in node.value else int)(node.value)

    def visit_string(self, node, children):
        # Remove trailing and leading double quotes
        return node.value[1:-1]

    def visit_nothing(self, node, children):
        return Nothing

    def visit_identifier(self, node, children):
        value = self.symbols[node.value]
        # None in the dictionary must be translated to "Nothing"
        # because None is indistinguishable from a token which
        # does not return a value at all to Arpeggio
        return value if value is not None else Nothing

    def visit_function(self, node, children):
        ret = self.functions[children[0]]() \
            if len(children) == 1           \
            else self.functions[children[0]](*children[1])
        return Nothing if ret is None else ret

    def visit_tuple_(self, node, children):
        # Remove the optional , at the end of a tuple e.g. "(1,)"
        # would result in [1, ","]
        if children[-1] == ",":
            children.pop()
        return tuple(children)

    def visit_factor(self, node, children):
        # If there is no + or - before an atom, we just return it
        if len(children) == 1:
            return children[0]
        sign = -1 if children[0] == "-" else 1
        return children[-1] * sign

    def visit_arglist(self, node, children):
        return children

    def visit_term(self, node, children):
        result = children[0]
        # Iterate over pairs of tokens
        for operator, operand in windows(children[1:], 2,2):
            if operator == "//":
                result //= operand
            elif operator == "/":
                result /= operand
            else:
               result *= operand
        return result

    def visit_arith(self, node, children):
        result = children[0]
        # Iterate over pairs of tokens
        for operator, operand in windows(children[1:],2,2):
            if operator == "+":
                result += operand
            else:
                result -= operand
        return result

    def visit_comparison(self, node, children):
        # Account for the single expression case
        if len(children) == 1:
            return children[0]

        # With the tokens ['7', '<', '6', '<', '5'] we iterate over the windows
        # ['7 > 6', '6 > 5'] which allows us to mimic the Python feature wherein
        # 7 > 6 > 5 evaluates to True rather than (5 > 6) > 7 == 1 > 7 == False
        for window in windows(children,3,2):
            if window[1] == "<" and not window[0] < window[2]: return 0
            if window[1] == ">" and not window[0] > window[2]: return 0
            if window[1] == "==" and not window[0] == window[2]: return 0
            if window[1] == "!=" and not window[0] != window[2]: return 0
            if window[1] == "<=" and not window[0] <= window[2]: return 0
            if window[1] == ">=" and not window[0] >= window[2]: return 0
        return 1

    def visit_assignment(self, node, children):
        # If this is just a single expression, just return the value
        if len(children) == 1:
            return children[0]

        if children[0] in self.reserved_keywords:
            # TODO: Probably should make out own excceptions
            raise ArpeggioError("Cannot redefine reserved keyword")

        # Store "Nothing"s as None in symbols dict for interoperability with other Python code
        self.symbols[children[0]] = None if children[1] is Nothing else children[1]
        return children[1]


if __name__ == "__main__":
    import sys
    from pprint import pprint

    debug = False
    parser = ParserPython(config, comment, debug=debug)
    parse_tree = parser.parse(sys.stdin.read())
    visitor = Config50Visitor(functions, debug=debug)
    visit_parse_tree(parse_tree, visitor)
    pprint(visitor.symbols)
