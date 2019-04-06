import enum
import itertools
import json

import attr
import lark
import pkg_resources

# todo: signed numbers
# todo: string quoted members
# todo: last - number  (ibm)
# todo: $."$varname" uses the variable name as lookup key
# todo: json string Unicode escapes
# todo: match json string semantics (\n and other escapes)
# todo: arithmetic expressions
# todo: list subscripts can be expressions
# todo: a lot more :)

grammar = pkg_resources.resource_string(__package__, "sql_json.lark").decode()
parser = lark.Lark(grammar, parser="lalr", start="query", debug=True)


class QueryError(Exception):
    pass


def compile(input):
    print(input)
    try:
        tree = parser.parse(input)
    except lark.UnexpectedInput as exc:
        raise QueryError(f"invalid query: {exc}") from exc
    print(tree.pretty())
    try:
        transformed = Transformer().transform(tree)
    except lark.exceptions.VisitError as exc:
        # The VisitError masks the underlying cause. Fortunately the original
        # exception is available from .context, so use that as the direct cause.
        raise QueryError(f"invalid query: {exc.__context__}") from exc.__context__
    print(transformed)
    return transformed


def query(query, context):
    return compile(query)(context)


class QueryMode(enum.Enum):
    lax = enum.auto()
    strict = enum.auto()


class PathType(enum.Enum):
    absolute = enum.auto()
    relative = enum.auto()


@attr.s(kw_only=True)
class Query:
    mode = attr.ib(default=QueryMode.lax)
    path = attr.ib()

    def __call__(self, context):
        return self.path(context, mode=self.mode)


@attr.s(kw_only=True)
class Path:
    steps = attr.ib(factory=list)
    type = attr.ib(default=PathType.absolute)

    def __call__(self, context, *, mode):
        objs = [context]
        for step in self.steps:
            new = []
            for obj in objs:
                new.extend(step(obj))
            objs = new

        return objs


@attr.s(kw_only=True)
class Step:
    def __call__(self, obj):
        raise NotImplementedError


@attr.s(kw_only=True)
class Member(Step):
    name = attr.ib()

    def __call__(self, obj):
        assert isinstance(obj, dict)
        yield obj[self.name]


@attr.s(kw_only=True)
class WildcardMember(Step):
    def __call__(self, obj):
        assert isinstance(obj, dict)
        yield from obj.values()


@attr.s(kw_only=True)
class Element(Step):
    index = attr.ib()

    def __call__(self, obj):
        assert isinstance(obj, list)
        yield obj[self.index]


@attr.s(kw_only=True)
class WildcardElement(Step):
    def __call__(self, obj):
        assert isinstance(obj, list)
        yield from obj


@attr.s(kw_only=True)
class RangesElement(Step):
    ranges = attr.ib()

    @ranges.validator
    def validate(self, attribute, value):
        assert value
        for start, stop in value:
            if start is not None and stop is not None and stop != -1 and start > stop:
                raise ValueError(f"invalid range: {start} to {stop}")

    def __call__(self, obj):
        # todo how to deal with out of range values?
        assert isinstance(obj, list)
        selectors = [False for _ in range(len(obj))]
        for start, stop in self.ranges:
            assert (start, stop) != (None, None)
            if start is None:
                r = range(0, stop)
            elif stop is None:
                r = range(start, len(obj))
            else:
                r = range(start, stop)
            for i in r:
                selectors[i] = True
        yield from itertools.compress(obj, selectors)


class Transformer(lark.Transformer):
    def query(self, children):
        if isinstance(children[0], QueryMode):
            mode, path = children
        else:
            (path,) = children
            mode = QueryMode.lax
        return Query(path=path, mode=mode)

    def path(self, steps):
        return Path(steps=steps)

    @lark.v_args(inline=True)
    def mode(self, s):
        return QueryMode[s]

    @lark.v_args(inline=True)
    def member(self, name=None):
        if name is None:
            return WildcardMember()
        else:
            return Member(name=name)

    @lark.v_args(inline=True)
    def member_name(self, name):
        return str(name)

    @lark.v_args(inline=True)
    def member_name_quoted(self, quoted_name):
        name, pos = json.decoder.scanstring(quoted_name, 1)
        assert pos == len(quoted_name)
        return name

    def element(self, ranges):
        if not ranges:
            return WildcardElement()

        if len(ranges) == 1:
            if len(ranges[0]) == 1:
                return Element(index=ranges[0][0])
            if ranges[0] == (0, None):  # 0 to last
                return WildcardElement()

        ranges = [normalize_range(r) for r in ranges]
        return RangesElement(ranges=ranges)

    def element_range(self, indices):
        return tuple(indices)

    @lark.v_args(inline=True)
    def element_index(self, s=None):
        if s is None:
            return None  # last
        return int(s)

    @lark.v_args(inline=True)
    def method(self, name):
        return "somemethod"  # todo

    def __getattr__(self, name):
        raise NotImplementedError(f"no transformer for {name}")


def normalize_range(indices):
    try:
        start, stop = indices
    except ValueError:
        (n,) = indices
        if n is None:
            start, stop = -2, -1
        else:
            start, stop = n, n + 1
    return start, stop
