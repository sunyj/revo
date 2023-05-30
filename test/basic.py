import unittest, json
from revo import Revo, _revo

class TestBasic(unittest.TestCase):

    def test_override_parse(self):
        self.assertEqual(_revo._parse_overrides('a=123'), {'a': 123})
        self.assertEqual(_revo._parse_overrides('a=xyz'), {'a': 'xyz'})
        self.assertEqual(_revo._parse_overrides('a="123"'), {'a': '123'})


    def test_parse_path(self):
        path = _revo._revo_path('abc/0/xyz')
        self.assertEqual(path, ['abc', 0, 'xyz'])


    def test_revo_path(self):
        doc = {'a': {'b': {'c': 123}}}
        self.assertEqual(_revo._revo_get(doc, 'a/b/c'), 123)

        doc = {'a': {'b': ['123', {'c': 123}]}}
        self.assertEqual(_revo._revo_get(doc, 'a/b/0'), '123')
        self.assertEqual(_revo._revo_get(doc, 'a/b/1/c'), 123)

        _revo._revo_set(doc, 'a/b/0', 'great')
        self.assertEqual(_revo._revo_get(doc, 'a/b/0'), 'great')
        _revo._revo_set(doc, 'a/b/1/c', 'world')
        self.assertEqual(_revo._revo_get(doc, 'a/b/1/c'), 'world')

        _revo._revo_del(doc, 'a/b/1')
        self.assertEqual(doc, {'a': {'b': ['great']}})


    def test_resolve(self):
        obj = Revo(json.loads("""
{
  "name": "test",
  "path": "/path/of/$(name)/$(date)",
  "conf": {
    "param": "some-$(date)",
    "aaa": "$(date)",
    "bbb": "$(nil)"
  },
  "def": {
    "x1": "na",
    "x2": "me"
  },
  "yyy": "$($(def/x1)$(def/x2))"
}
"""), ['date=20210702'])
        self.assertEqual(obj['name'], 'test')
        self.assertEqual(obj['conf/aaa'], 20210702)
        self.assertTrue(isinstance(obj['conf'], dict))
        self.assertEqual(obj['path'], '/path/of/test/20210702')
        self.assertEqual(obj['yyy'], 'test')


### test/basic.py ends here
