from protojit import Serializer


def _test(x):
    s = Serializer(x)
    assert s.deserialize(s.serialize(x)) == x


def test_basic():
    _test({'a': 1, 'b': '2', 'c': True})


def test_nested():
    _test({'a': {'b': 'c'}})


def test_list():
    _test({'a': [1, 2]})


def test_list_nested():
    _test({'a': [{'b': 'c'}]})
