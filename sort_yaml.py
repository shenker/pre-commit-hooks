#!/usr/bin/env python
"""Sort a YAML file, keeping blocks of comments and definitions
together.
"""
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
import argparse
import sys
from collections.abc import Mapping


class StringYAML(YAML):
    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()


def _sort_key(x):
    if isinstance(x, Mapping):
        return next(iter(x.keys()))
    else:
        return x


# FROM: https://stackoverflow.com/questions/51386822/how-to-recursively-sort-yaml-using-commentedmap
def sort_mappings(s, recursive=False, sort_lists=True):
    if isinstance(s, list):
        for elem in s:
            if recursive:
                sort_mappings(elem, recursive=recursive)
        if sort_lists:
            s[:] = sorted(s, key=_sort_key)
        return
    if not isinstance(s, dict):
        return
    for key in sorted(s, reverse=True, key=_sort_key):
        value = s.pop(key)
        if recursive:
            sort_mappings(value, recursive=recursive)
        s.insert(0, key, value)


def process_yaml(doc, keys=None, recursive=False):
    if keys:
        for key in keys:
            d = doc[key]
            print(key, d)
            sort_mappings(d, recursive=recursive)
    else:
        sort_mappings(doc, recursive=recursive)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    parser.add_argument(
        '-r',
        '--recursive',
        default=False,
        action='store_true',
        help="Sort YAML recursively",
    )
    parser.add_argument(
        '-k', '--key', type=str, action='append', help="YAML keys to sort"
    )
    args = parser.parse_args(argv)
    retval = 0
    yaml = StringYAML()
    yaml.indent(mapping=4, sequence=4, offset=2)
    for filename in args.filenames:
        with open(filename, 'r+') as f:
            old_contents = f.read()
            doc = yaml.load(old_contents)
            process_yaml(doc, keys=args.key, recursive=args.recursive)
            new_contents = yaml.dump(doc)
            if old_contents != new_contents:
                print(f'Fixing file `{filename}`')
                f.seek(0)
                f.write(new_contents)
                f.truncate()
                retval = 1

    return retval


if __name__ == '__main__':
    exit(main())
