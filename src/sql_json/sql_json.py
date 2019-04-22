import ast
import enum
import itertools
import json
import operator

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
# todo: case insensitive keywords? (allowed at all?)
# todo: list subscripts can be expressions
# todo: a lot more :)


grammar = pkg_resources.resource_string(__package__, "grammar.lark").decode()
parser = lark.Lark(grammar, parser="lalr", start="expression", debug=True)

OPERATOR_MAP = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
}


def query(query, context):
    return compile(query)(context)


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


class Error(Exception):
    """
    Base SQL/JSON exception class.
    """

    pass


class QueryError(Error):
    """
    Exception raised for problematic queries.
    """

    pass


class Transformer(lark.Transformer):
    def __getattr__(self, name):
        raise NotImplementedError(f"no transformer for {name}")

    @lark.v_args(inline=True)
    def _return_expr(self, expr):
        """Helper to return the child expression."""
        return expr

    accessor_op = _return_expr
    primary = _return_expr
    variable = _return_expr
    wff = _return_expr

    def expression(self, args):
        try:
            mode, expr = args
        except ValueError:
            (expr,) = args
            mode = QueryMode.lax
        return Query(expr=expr, mode=mode)

    @lark.v_args(inline=True)
    def mode(self, s):
        return QueryMode[s]

    @lark.v_args(inline=True)
    def context_variable(self):
        return ContextVariable()

    @lark.v_args(inline=True)
    def key_name(self, name):
        return str(name)

    @lark.v_args(inline=True)
    def string_literal(self, value):
        return json.loads(value)

    @lark.v_args(inline=True)
    def member_accessor(self, name):
        return MemberAccessor(member=name)

    @lark.v_args(inline=True)
    def accessor_expression(self, expr, accessor=None):
        if accessor is None:
            return expr

        accessor.expr = expr
        return accessor

    def unary_expression(self, args):
        try:
            op, expr = args
            assert op in ("-", "+")
            if op == "-":
                expr = MinusOperator(expr=expr)
        except ValueError:
            (expr,) = args
        return expr

    def multiplicative_expression(self, args):
        try:
            left, op, right = args
            expr = BinaryOperator(left=left, op=OPERATOR_MAP[op], right=right)
        except ValueError:
            (expr,) = args
        return expr

    additive_expression = multiplicative_expression

    @lark.v_args(inline=True)
    def literal(self, value):
        expr = Constant(value=value)
        return expr

    @lark.v_args(inline=True)
    def numeric_literal(self, s):
        return ast.literal_eval(s)

    @lark.v_args(inline=True)
    def _(self, *args):
        __import__("pdb").set_trace()  # FIXME
        assert 0

    # def path(self, steps):
    #     # todo
    #     return Path(steps=steps)

    # @lark.v_args(inline=True)
    # def member_name(self, name):
    #     # todo
    #     return str(name)

    # def element(self, ranges):
    #     # todo
    #     if not ranges:
    #         return WildcardElement()
    #     return RangesElement(ranges=ranges)

    # @lark.v_args(inline=True)
    # def element_single_or_range(self, x):
    #     # todo
    #     return x

    # @lark.v_args(inline=True)
    # def element_single(self, index):
    #     # todo
    #     if index is None:  # last
    #         return (-1, None)
    #     else:
    #         return index, index + 1

    # @lark.v_args(inline=True)
    # def element_range(self, start, stop):
    #     # todo
    #     if start is None:
    #         if stop is None:  # e.g. $[last to last]
    #             start = -1
    #         else:  # e.g. $[last to 5]
    #             raise ValueError(f"invalid range: last to {stop}")
    #     elif stop is not None and start > stop:
    #         raise ValueError(f"invalid range: {start} to {stop}")
    #     return start, stop

    # @lark.v_args(inline=True)
    # def element_index(self, s=None):
    #     # todo
    #     if s is None:
    #         return None  # e.g. $[last]
    #     return int(s)  # e.g. $[4]

    # @lark.v_args(inline=True)
    # def method(self, name, *args):
    #     # todo
    #     __import__("pdb").set_trace()  # FIXME
    #     return name, args  # todo


class QueryMode(enum.Enum):
    lax = enum.auto()
    strict = enum.auto()


@attr.s(kw_only=True)
class Node:
    pass


@attr.s(kw_only=True)
class Query(Node):
    mode = attr.ib(default=QueryMode.lax)
    expr = attr.ib()


@attr.s(kw_only=True)
class Constant(Node):
    value = attr.ib()


@attr.s(kw_only=True)
class Variable(Node):
    pass


@attr.s(kw_only=True)
class ContextVariable(Variable):
    pass


@attr.s(kw_only=True)
class NamedVariable(Variable):
    name = attr.ib()


@attr.s(kw_only=True)
class Accessor(Node):
    expr = attr.ib(default=None)


@attr.s(kw_only=True)
class MemberAccessor(Accessor):
    member = attr.ib()

    def __call__(self, obj):
        assert isinstance(obj, dict)
        yield obj[self.member]


@attr.s(kw_only=True)
class WildcardMemberAccessor(Accessor):
    def __call__(self, obj):
        assert isinstance(obj, dict)
        yield from obj.values()


@attr.s(kw_only=True)
class ArrayAccessor(Accessor):
    ranges = attr.ib()

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


@attr.s(kw_only=True)
class WildcardArrayAccessor(Accessor):
    def __call__(self, obj):
        assert isinstance(obj, list)
        yield from obj


@attr.s(kw_only=True)
class UnaryOperator(Node):
    pass


@attr.s(kw_only=True)
class MinusOperator(UnaryOperator):
    expr = attr.ib()


@attr.s(kw_only=True)
class BinaryOperator(Node):
    op = attr.ib()
    left = attr.ib()
    right = attr.ib()


@attr.s(kw_only=True)
class BooleanOperator(Node):
    op = attr.ib()
    values = attr.ib()


@attr.s(kw_only=True)
class Method(Node):
    pass


@attr.s(kw_only=True)
class TypeMethod(Method):
    pass


@attr.s(kw_only=True)
class SizeMethod(Method):
    pass


@attr.s(kw_only=True)
class DoubleMethod(Method):
    pass


@attr.s(kw_only=True)
class CeilingMethod(Method):
    pass


@attr.s(kw_only=True)
class FloorMethod(Method):
    pass


@attr.s(kw_only=True)
class AbsMethod(Method):
    pass


@attr.s(kw_only=True)
class DatetimeMethod(Method):
    template = attr.ib()


@attr.s(kw_only=True)
class KeyValuesMethod(Method):
    pass
