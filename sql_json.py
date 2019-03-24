import enum
import json

import attr
import lark

grammar = r"""
    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.INT
    %import common.WS

    %ignore WS

    json_path: [mode] absolute_path

    mode: "strict" -> mode_strict
        | "lax" -> mode_lax

    absolute_path: "$" path
    relative_path: "@" path
    path: step*

    ?step: member | element | filter | method

    member: "." ("*" | member_name | member_name_quoted)
    member_name: CNAME
    member_name_quoted: ESCAPED_STRING

    element: "[" ("*" | _element_ranges) "]"
    _element_ranges: element_range ("," element_range)*
    element_range: element_index ["to" element_index]
    element_index: INT | "last"

    filter: "TODO"

    method: "." CNAME "()"
    """

# todo: signed numbers
# todo: string quoted members
# todo: last - number  (ibm)
# todo: $."$varname" uses the variable name as lookup key
# todo: json string Unicode escapes
# todo: match json string semantics (\n and other escapes)

parser = lark.Lark(grammar, parser="lalr", start="json_path", debug=True)


def parse(input):
    tree = parser.parse(input)
    print(tree.pretty())
    transformed = Transformer().transform(tree)
    print(transformed)
    return transformed


@attr.s(slots=True)
class ASTNode:
    pass


class PathMode(enum.Enum):
    strict = enum.auto()
    lax = enum.auto()


class PathType(enum.Enum):
    absolute = enum.auto()
    relative = enum.auto()


@attr.s(slots=True)
class Path(ASTNode):
    steps = attr.ib(factory=list)
    type = attr.ib(PathType.absolute)
    mode = attr.ib(default=PathMode.strict)


@attr.s(slots=True)
class Member(ASTNode):
    name = attr.ib()


@attr.s(slots=True)
class Element(ASTNode):
    ranges = attr.ib()


class Transformer(lark.Transformer):
    def json_path(self, children):
        if isinstance(children[0], PathMode):
            mode, path = children
            path.mode = mode
        else:
            (path,) = children
        return path

    def absolute_path(self, children):
        (path,) = children
        path.type = PathType.absolute
        return path

    def relative(self, children):
        (path,) = children
        path.type = PathType.relative
        return path

    def path(self, steps):
        return Path(steps=steps)

    def mode_lax(self, children):
        # todo: use one method for lax/strict and do enum lookup
        return PathMode.lax

    def mode_strict(self, children):
        return PathMode.strict

    def member(self, names):
        if not names:
            name = None  # wildcard
        else:
            (name,) = names
        return Member(name=name)

    def member_name(self, children):
        (name,) = children
        return str(name)

    def member_name_quoted(self, children):
        (quoted_name,) = children
        name, end = json.decoder.scanstring(quoted_name, 1)
        assert end == len(quoted_name)
        return name

    def element(self, ranges):
        if not ranges:
            ranges = None  # wildcard
        return Element(ranges=ranges)

    def element_range(self, indexes):
        n_indexes = len(indexes)
        if n_indexes == 0:
            start = end = None
        elif n_indexes == 1:
            start = end = indexes[0]
        else:
            start, end = indexes
        return start, end

    def element_index(self, children):
        if not children:
            return None  # last
        (s,) = children
        return int(s)

    def method(self, children):
        return "somemethod"  # todo

    def __getattr__(self, name):
        raise NotImplementedError(f"no transformer for {name}")
