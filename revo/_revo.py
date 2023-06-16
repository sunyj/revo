################################################################################
# revo --- Referenced Values in Objects
################################################################################
__all__ = ['Revo']

import re
import ast
from copy import deepcopy
try:
    from collections.abc import MutableMapping
except:
    from collections import MutableMapping


def _parse_literal(spec):
    try:
        return ast.literal_eval(spec)
    except:
        return spec


def _parse_overrides(spec):
    if not spec:
        return {}
    if isinstance(spec, dict):
        return spec
    if isinstance(spec, str):
        return _parse_overrides([spec])
    return {s[0]: _parse_literal('='.join(s[1:]))
            for s in [x.split('=') for x in spec] if len(s) >= 1}


def _revo_path(spec):
    return [_parse_literal(x) for x in spec.split('/')]


def _revo_get(obj, path, orig_path=None):
    if not isinstance(path, list):
        return _revo_get(obj, _revo_path(path))
    if not orig_path:
        orig_path = path
    if not path:
        return obj
    key = path[0]
    if isinstance(key, str) and key not in obj:
        raise KeyError(f'path "{"/".join(orig_path)}" not found')
    return _revo_get(obj[key], path[1:], orig_path)


def _revo_set(obj, path, val, extend=True, orig_path=None):
    if not isinstance(path, list):
        _revo_set(obj, _revo_path(path), val, extend)
        return
    if not orig_path:
        orig_path = path
    key = path[0]
    if len(path) == 1:
        if not extend and isinstance(key, str) and key not in obj:
            raise KeyError(f'path "{"/".join(orig_path)}" not found')
        obj[key] = val
    else:
        _revo_set(obj[key], path[1:], val, extend, orig_path)


def _revo_del(obj, path):
    if not isinstance(path, list):
        return _revo_del(obj, _revo_path(path))
    if len(path) == 1:
        del obj[path[0]]
    else:
        _revo_del(obj[path[0]], path[1:])


def _revo_melt(obj):
    "break down an object into flat key-value pairs"

    if isinstance(obj, dict):
        for key, val in obj.items():
            for k, v in _revo_melt(val):
                yield (f'{key}/{k}', v) if k else (key, val)
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            for k, v in _revo_melt(val):
                yield (f'{idx}/{k}', v) if k else (str(idx), val)
    else:
        yield (None, obj)


class Revo(MutableMapping):

    def __init__(self, obj, overrides=None, *,
                 mercy=False, absorb=False, retain=True, extend=True):
        self.val = deepcopy(obj)
        if not isinstance(obj, (list, dict)):
            raise TypeError('Only list or dict object allowed')

        self.mercy  = mercy   # allow unresolved or illegal references
        self.absorb = absorb  # merge definitions into the tree
        self.retain = retain  # try to keep reference value type
        self.extend = extend  # allow extending new leaf nodes

        # top-level overrides not found in original object are definitions
        self.defs = []

        if overrides:
            self.resolve(overrides)


    def override(self, spec):
        for key, val in _parse_overrides(spec).items():
            # treat new top-level keys as definitions
            if '/' not in key and key not in self.val:
                self.val[key] = val
                if not self.absorb:
                    self.defs.append(key)
            else:
                self[key] = val

        return self


    def resolve(self, override_spec=None):
        # apply overrides
        if override_spec:
            self.override(override_spec)

        # resolve value references bottom-up
        flat = {key: val for key, val in self.melt()}
        while any('$(' in str(val) for val in flat.values()):
            subs = list(flat.keys())
            changed = 0
            for sub in subs:
                var = f'$({sub})'
                for key, val in flat.items():
                    val = str(val)
                    if var in val:
                        if key == sub:
                            if self.mercy:
                                continue
                            raise ValueError(f'self-reference of {sub}')
                        changed += 1
                        if self.retain and val == var:
                            self[key] = flat[sub]
                        else:
                            self[key] = val.replace(var, str(flat[sub]))
            if not changed:
                break
            flat = {key: val for key, val in self.melt()}

        # remove definitions
        for key in self.defs:
            del self[key]

        # mercy on unresolved or illegal references?
        if not self.mercy:
            for key, val in self.melt():
                if '$(' not in str(val):
                    continue
                mo = re.search(r'(\$\([^)]+\))', val)
                if not mo:
                    err = f'illegal reference "{val}" (from {key})'
                else:
                    err = f'reference {mo.group(1)} unresolved (from {key})'
                raise ValueError(err)

        return self


    def melt(self):
        return _revo_melt(self.val)


    def __getitem__(self, key): return _revo_get(self.val, key)
    def __setitem__(self, key, val): _revo_set(self.val, key, val, self.extend)
    def __delitem__(self, key): _revo_del(self.val, key)
    def __iter__(self): return iter(self.val)
    def __len__(self): return len(self.val)
    def __str__(self): return str(self.val)
    def __repr__(self): return repr(self.val)

### revo.py ends here
