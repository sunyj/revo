# Revo – *Re*ferenced *V*alues in *O*bjects

**Revo** is a non-intrusive variable substitution solution for config files.

**Revo** is [listed on PyPI](https://pypi.org/project/revo/).

**Revo** casts a Python built-in `dict` or `list` into a mutable tree, where the
value of each tree node is either a string or a number, while any node can
reference any other node in the tree with GNU make style `$(var)` variable
syntax.

Although a tiny (under 200 lines of code) library, **revo** provides some
level of programmability to plain old Python objects and thus great
flexibility to many applications, especially configuration processing. No
matter what format (`JSON`, `YAML`, `TOML`, etc.) your config file is, as long
as it maps to Python built-in types cleanly, **revo** provides Makefile-style
variable substitution to it.


# Design ideas

**Revo** treats a Python built-in object as a tree of data, like an XML
doc. The top-level object must be `dict` or `list`. Values on tree nodes must
be either `str`, `bool`, or built-in number (`int` or `float`).

In order to reference *any* node in an object tree, we need to design a path
mechanism. Yes, the idea is like [XPath](https://en.wikipedia.org/wiki/XPath)
for Python objects, but much simpler.

In fact, we can almost simply borrow the design of UNIX path: slash-separated
string, with only a small adaptation: path segments in integer literals are
treated as numeric indexes for `list`.

An exmple would be nice, isn't it?

```python
# This is legal Python code, making an object from literals.
# You can also construct it from a YAML or JSON file.
conf = {
  "project": {
    "name": "revo",
    "version": "0.1.0",
    "rules": {
      "Homepage": "https://github.com/sunyj/$(project/name)"
    }
  },
  "classifiers": [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent"
  ],
  "tag": "$(classifiers/0)", # reference a list element with integer index
  "v1": "project",
  "v2": "version",
  "v3": "$($(v1)/$(v2))" # support variables in variable names
}

# Resolve variable references with revo
from revo import Revo
obj = Revo(conf).resolve()

print(obj['project/rules/Homepage'])  # https://github.com/sunyj/revo
print(obj['tag'])                     # Programming Language :: Python :: 3
print(obj['v3'])                      # 0.1.0
```


# Typical use cases


Almost everyone who works long enough with config files appreciates the great
value of a robust and flexible variable substitution mechanism. It helps to
reduce tedious config-processing logic by moving them to config files.

Revo was designed to be a non-intrusive solution for that purpose. It resolves
on Python objects, not the files storing those objects, so it's transparent to
the config file format.


# Design details

The core mechanism is the path to reach any node in the object tree. With a
unique path for every node, an object can be melted down to a set of flat dict
of key-value mappings. The definition of class `Revo` reflects that.

```python
class Revo(MutableMapping):
    ... ...
```

As the path of every node is unique within an object, it may serve as the
*name* for the corresponding node's value. Voilà! *variable*, as in the
context of "*variable substitution*", can now be properly defined.

| Concept        | Implementation |
| -------------- | -------------- |
| variable       | tree node      |
| variable name  | node path      |
| variable value | node value     |

[Variables Make Makefiles Simpler](https://www.gnu.org/software/make/manual/html_node/Variables-Simplify.html),
equally true for config files. We simply use the variable reference syntax of
[GNU make](https://www.gnu.org/software/make/).


## Variable overrides

Another common need for config files is overriding values from command line or
other input sources. **Revo** supports that with its `override` method:

```python
from revo import Revo
override_specs = ['date=20200110', 'conf/path=/another/path/with=/in/it']

# construct with overrides
conf_obj = load_my_json_config(...)
conf = Revo(conf_obj, override_specs)

# or in a separate call
conf = Revo(load_my_yaml_config(...))
conf.override(override_specs).resolve()
```

Override spec parsing rules:
- First `=` is used as the name-value separator. Subsequent `=` characters are all put into the value string.
- Revo always tries parsing the value string as a Python literal, and falls back to string if that fails.


## Fault tolerance

Keyword-only boolean argument `mercy` controls if **revo** raises exceptions
on errors during the resolution process. Typical errors are:

- Unknown variable.
- Illegal variable syntax.
- Self-reference or circular reference.

It defaults to `False`.  When `mercy=True`, unresolved or partially-resolved
values are left in the object.


## Definition merging

Overrides may contain variables that are not in the object under resolve, for
example:

```python
import revo
conf = revo.Revo({'name': 'hello $(date)'}, ['date=20220101'])
conf['name'] # 'hello 20220101'
conf['date'] # what do you expect?
```

Such overrides are called *definitions*.  Definitions may stay in the object
after the resolution.  Keyword-only boolean argument `absorb` controls this,
it defaults to `False`.


## Type retaining

Keyword-only boolean argument `retain` controls if **revo** tries to keep
variable value type in substitutions.

It defaults to `True`.  When `retain=False`, values resolved are always `str`.

```python
import revo
conf = revo.Revo({'name': 'n$(val)', 'x': '$(val)', 'val': 10}, retain=True)
conf.resolve()

type(conf['name'])  # <class 'str'>
type(conf['x'])     # <class 'int'>
```

# Limitations

Variable substitutions are resolved bottom-up, which means **revo** copies and
iterates over all values in loops until no more incremental substitution
happens. This algorithm is easy to understand and implement, but it's pretty
slow. For average config files with typically dozens or hundreds of entries,
performance should not be a concern on modern computers. However, if you plan
to use it on very large config files, make performance tests before you invest
further.
