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
    r'$."foo\u2603".*',
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
    _tree = sql_json.compile(test_input)
    # __import__("IPython").embed()  # FIXME


def test_query():
    doc = {"foo": {"bar": {"baz": 123}}}
    query = sql_json.compile("$.foo.bar.baz")
    assert query(doc) == 123
