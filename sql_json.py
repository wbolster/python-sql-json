import lark

grammar = r"""
    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.INT
    %import common.WS

    %ignore WS

    start: json_path_expr

    json_path_expr: [mode] absolute_path_expr
    !mode: "strict" | "lax"

    absolute_path_expr: "$" path_expr
    relative_path_expr: "@" path_expr
    path_expr: step*

    step: member | element | filter | method

    member: "." ("*" | CNAME | ESCAPED_STRING)

    element: "[" (element_wildcard | element_ranges) "]"
    element_wildcard: "*"
    element_ranges: element_range ("," element_range)*
    !element_range: ELEMENT_INDEX ["to" ELEMENT_INDEX]
    ELEMENT_INDEX: INT | "last"

    filter: "TODO"

    method: "." CNAME "()"
    """

# todo: signed numbers
# todo: string quoted members
# todo: last - number  (ibm)

parser = lark.Lark(grammar, parser="lalr", debug=True)


def parse(input):
    parsed = parser.parse(input)
    return parsed
