################################################################################
# revo --- Referenced Values in Objects
################################################################################
__all__ = ['Revo']

import re
import ast
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


def _revo_set(obj, path, val, orig_path=None):
    if not isinstance(path, list):
        _revo_set(obj, _revo_path(path), val)
        return
    if not orig_path:
        orig_path = path
    key = path[0]
    if len(path) == 1:
        if isinstance(key, str) and key not in obj:
            raise KeyError(f'path "{"/".join(orig_path)}" not found')
        obj[key] = val
    else:
        _revo_set(obj[key], path[1:], val, orig_path)


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
                yield (f'{idx}/{k}', v) if k else (key, val)
    else:
        yield (None, obj)


class Revo(MutableMapping):
    def __init__(self, obj, overrides=None, *, mercy=True, merge_defs=False):
        self.val = obj
        if not isinstance(obj, (list, dict)):
            raise TypeError('Only list or dict object allowed')
        if overrides:
            self.resolve(overrides, mercy=mercy, merge_defs=merge_defs)


    def melt(self):
        return _revo_melt(self.val)


    def resolve(self, override_spec=None, *, mercy=True, merge_defs=False):
        # top-level overrides not found in original object are definitions
        defs = []

        # apply overrides
        if override_spec:
            for key, val in _parse_overrides(override_spec).items():
                # treat new top-level keys as definitions
                if '/' not in key and key not in self.val:
                    self.val[key] = val
                    if not merge_defs:
                        defs.append(key)
                else:
                    self[key] = val

        # resolve value references
        flat = {key: str(val) for key, val in self.melt()}
        while any('$(' in val for val in flat.values()):
            subs = list(flat.keys())
            changed = 0
            for sub in subs:
                for key, val in flat.items():
                    if f'$({sub})' in val:
                        if key == sub:
                            raise ValueError(f'self-reference of {sub}')
                        changed += 1
                        self[key] = val.replace(f'$({sub})', flat[sub])
            if not changed:
                break
            flat = {key: str(val) for key, val in self.melt()}

        # remove definitions
        for key in defs:
            del self[key]

        # mercy on unresolved or illegal references?
        if not mercy:
            for key, val in self.melt():
                if '$(' not in val:
                    continue
                mo = re.search(r'(\$\(.+\))', val)
                if not mo:
                    err = f'illegal reference "{val}" (from {key})'
                else:
                    err = f'reference {mo.group(1)} unresolved (from {key})'
                raise ValueError(err)


    def __getitem__(self, key): return _revo_get(self.val, key)
    def __setitem__(self, key, val): _revo_set(self.val, key, val)
    def __delitem__(self, key): _revo_del(self.val, key)
    def __iter__(self): return iter(self.val)
    def __len__(self): return len(self.val)
    def __str__(self): return str(self.val)
    def __repr__(self): return repr(self.val)


### revo.py ends here
