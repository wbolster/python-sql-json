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
    mode: MODE
    MODE: "strict" | "lax"

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
    try:
        transformed = Transformer().transform(tree)
    except lark.exceptions.VisitError as exc:
        if exc.__context__ is not None:
            raise exc.__context__ from None
        else:
            raise
    print(transformed)
    return transformed


@attr.s(slots=True)
class ASTNode:
    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.validate()
        return instance

    def validate(self):
        pass


class PathMode(enum.Enum):
    lax = enum.auto()
    strict = enum.auto()


class PathType(enum.Enum):
    absolute = enum.auto()
    relative = enum.auto()


@attr.s(slots=True)
class Path(ASTNode):
    steps = attr.ib(factory=list)
    type = attr.ib(default=PathType.absolute)
    mode = attr.ib(default=PathMode.lax)


@attr.s(slots=True)
class Member(ASTNode):
    name = attr.ib()


@attr.s(slots=True)
class Element(ASTNode):
    ranges = attr.ib()

    def validate(self):
        if self.ranges is None:
            return
        for start, end in self.ranges:
            if start is not None and end is not None and start > end:
                raise ValueError(f"invalid range: {start} to {end}")


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
        return Path.create(steps=steps)

    def mode(self, children):
        (s,) = children
        return PathMode[s]

    def member(self, names):
        if not names:
            name = None  # wildcard
        else:
            (name,) = names
        return Member.create(name=name)

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
        return Element.create(ranges=ranges)

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
