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
  "array": [
    "hello",
    "world"
  ],
  "yyy": "$($(def/x1)$(def/x2))",
  "line": "$(array/1)"
}
"""), ['date=20210702'], mercy=True)
        self.assertEqual(obj['name'], 'test')
        self.assertEqual(obj['conf/aaa'], 20210702)
        self.assertTrue(isinstance(obj['conf'], dict))
        self.assertEqual(obj['path'], '/path/of/test/20210702')
        self.assertEqual(obj['yyy'], 'test')
        self.assertEqual(obj['line'], 'world')


    def test_immutable(self):
        obj = {'data': {'name': 'foo'}}
        conf = Revo(obj, overrides=['data/func=bar'])
        self.assertEqual(len(obj['data']), 1)
        self.assertEqual(len(conf.val['data']), 2)


    def test_empty_overrides(self):
        obj = Revo(json.loads("""
{
  "date": "some day",
  "pipe": {
    "ds": "file",
    "date": "$(date)"
  }
}
"""))
        self.assertEqual(obj['pipe']['date'], 'some day')


    def test_mercy_self_ref(self):
        data = {"date": "$(date)"}
        obj = Revo(data, mercy=True)
        self.assertEqual(data, obj)
        with self.assertRaises(ValueError):
            obj = Revo(data, mercy=False)


    def test_mercy_illegal(self):
        data = {"date": "2020", "pipe": {"date": "$(date"}}
        obj = Revo(data, mercy=True)
        self.assertEqual(data, obj)
        with self.assertRaises(ValueError):
            obj = Revo(data, mercy=False)


    def test_mercy_undefined(self):
        data = {"date": "2020", "pipe": {"date": "$(dates)"}}
        obj = Revo(data, mercy=True)
        self.assertEqual(data, obj)
        with self.assertRaises(ValueError):
            obj = Revo(data, mercy=False)


    def test_absorb(self):
        data = {
            "date": "some day",
            "pipe": {
                "ds": "file",
                "date": "$(date)"
            }
        }
        obj = Revo(data, ['period=empty'], absorb=True)
        self.assertEqual(obj['period'], 'empty')
        obj = Revo(data, ['period=empty'], absorb=False)
        self.assertTrue('period' not in obj)


    def test_retain(self):
        data = {
            "date": 20200101,
            "pipe": {
                "ds": "file",
                "date": "$(date)"
            }
        }
        obj = Revo(data, retain=True)
        self.assertEqual(obj['pipe']['date'], 20200101)
        self.assertTrue(isinstance(obj['pipe']['date'], int))
        obj = Revo(data, retain=False)
        self.assertEqual(obj['pipe']['date'], '20200101')
        self.assertTrue(isinstance(obj['pipe']['date'], str))


    def test_extend(self):
        data = {
            "date": "some day",
            "pipe": {
                "ds": "file",
                "date": "$(date)"
            }
        }
        obj = Revo(data, ['pipe/dst=/dev/null'], extend=True)
        self.assertEqual(obj['pipe']['dst'], '/dev/null')
        with self.assertRaises(KeyError):
            obj = Revo(data, ['pipe/dst=/dev/null'], extend=False)

### test/basic.py ends here
