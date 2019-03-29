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
    "$[0 to last]",
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


def test_path_members():
    doc = {"foo": {"bar": {"baz": 123}}}
    query = "$.foo.bar.baz"
    assert sql_json.query(query, doc) == 123


def test_path_elements():
    doc = {"items": [1, 2, 3, 4, 5]}
    assert sql_json.query("$.items[0]", doc) == 1
    assert sql_json.query("$.items[*]", doc) == [1, 2, 3, 4, 5]
    assert sql_json.query("$.items[0 to last]", doc) == [1, 2, 3, 4, 5]
    assert sql_json.query("$.items[0 to 2]", doc) == [1, 2]
    assert sql_json.query("$.items[1 to 4]", doc) == [2, 3, 4]
    assert sql_json.query("$.items[4 to last]", doc) == [5]
