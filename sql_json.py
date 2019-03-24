import lark

grammar = r"""
    %import common.INT
    %import common.WS

    start: json_path_expr

    json_path_expr: _ws? [mode _ws] wff
    !mode: "strict" | "lax"

    wff: additive_expr

    UNARY_OPERATOR: "+" | "-"
    ADDITIVE_OPERATOR: "+" | "-"
    MULTIPLICATIVE_OPERATOR: "*" | "/" | "%"

    ?additive_expr: [additive_expr ADDITIVE_OPERATOR _ws?] multiplicative_expr
    ?multiplicative_expr: [multiplicative_expr MULTIPLICATIVE_OPERATOR _ws?] unary_expr
    ?unary_expr: (accessor_expr _ws? | UNARY_OPERATOR _ws? unary_expr)

    accessor_expr: absolute_path_expr | relative_path_expr

    absolute_path_expr: "$" path_expr
    relative_path_expr: "@" path_expr
    path_expr: step*

    step: member | element | filter | method

    member: "." ("*" | NAME)

    element: "[" _ws? (element_wildcard | element_ranges) "]"
    element_wildcard: "*" _ws?
    element_ranges: element_range ("," _ws? element_range)*
    !element_range: ELEMENT_INDEX [_ws "to" _ws ELEMENT_INDEX] _ws?
    ELEMENT_INDEX: INT | "last"

    filter: "TODO"

    method: "." NAME "()"

    NAME: /[A-Z_][A-Z0-9_]*/i
    _ws: WS
    """

# todo: signed numbers
# todo: string quoted members
# todo: last - number  (ibm)

parser = lark.Lark(grammar, parser="lalr", debug=True)


def parse(input):
    parsed = parser.parse(input)
    return parsed