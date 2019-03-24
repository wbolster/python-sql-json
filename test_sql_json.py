import pytest
import sql_json


TEST_INPUTS = [
    "$",
    "strict $",
    "lax $",
    "$.foo",
    "$.foo.bar.baz",
    "$.*",
    "$.foo.*",
    "$.*.foo",
    "$[*]",
    "$[ *]",
    "$[* ]",
    "$[3]",
    "$[last]",
    "$[0, 2]",
    "$[ 0, 2 ]",
    "$[0 to 2]",
    "$[0, 2, last]",
    "$[0, 2 to last]",
    "$[3].bar[*].baz",
    "$[*].bar[2 to 3, 4, last].baz",
    "$.size()",
]


@pytest.mark.parametrize("test_input", TEST_INPUTS)
def test_sql_json(test_input):
    print()
    print(test_input)
    parsed = sql_json.parse(test_input)
    print(parsed.pretty())
