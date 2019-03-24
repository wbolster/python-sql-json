import json

import attr
import lark

grammar = r"""
    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.INT
    %import common.WS

    %ignore WS

    json_path_expr: [MODE] absolute_path_expr
    MODE: "strict" | "lax"

    absolute_path_expr: "$" path_expr
    relative_path_expr: "@" path_expr
    path_expr: step*

    ?step: member | element | filter | method

    member: "." ("*" | member_name | member_name_quoted)
    member_name: CNAME
    member_name_quoted: ESCAPED_STRING

    element: "[" ("*" | _element_ranges) "]"
    _element_ranges: element_range ("," element_range)*
    element_range: ELEMENT_INDEX ["to" ELEMENT_INDEX]
    ELEMENT_INDEX: INT | "last"

    filter: "TODO"

    method: "." CNAME "()"
    """

# todo: signed numbers
# todo: string quoted members
# todo: last - number  (ibm)
# todo: $."$varname" uses the variable name as lookup key
# todo: json string Unicode escapes
# todo: match json string semantics (\n and other escapes)

parser = lark.Lark(grammar, parser="lalr", start="json_path_expr", debug=True)


class Node:
    pass


@attr.s
class Member(Node):
    name = attr.ib(default=None)


class Transformer(lark.Transformer):
    def member(self, children):
        return Member(*children)

    def member_name(self, children):
        (name,) = children
        return str(name)

    def member_name_quoted(self, children):
        (quoted_name,) = children
        name, end = json.decoder.scanstring(quoted_name, 1)
        assert end == len(quoted_name)
        return name


def parse(input):
    tree = parser.parse(input)
    print(tree.pretty())
    transformed = Transformer().transform(tree)
    print(transformed.pretty())
    return transformed
