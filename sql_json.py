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

    member: "." ("*" | CNAME | ESCAPED_STRING)

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


def parse(input):
    tree = parser.parse(input)
    return tree
