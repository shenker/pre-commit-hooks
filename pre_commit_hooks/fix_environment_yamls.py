#!/usr/bin/env python
"""Sort a YAML file, keeping blocks of comments and definitions
together.
"""
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from ruamel.yaml.comments import merge_attrib
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


# FROM: https://stackoverflow.com/a/62979508
# SEE ALSO: https://stackoverflow.com/questions/51386822/how-to-recursively-sort-yaml-using-commentedmap
def sort_mappings(s):
    if isinstance(s, list):
        for elem in s:
            sort_mappings(elem)
        s.sort(key=_sort_key)
        return
    if not isinstance(s, dict):
        return
    merge = getattr(s, merge_attrib, [None])[0]
    if merge is not None and merge[0] != 0:  # << not in first position, move it
        setattr(s, merge_attrib, [(0, merge[1])])

    for key in sorted(s._ok):  # _ok -> set of Own Keys, i.e. not merged in keys
        value = s[key]
        sort_mappings(value)
        s.move_to_end(key)


def process_file(doc):
    if "prefix" in doc:
        del doc["prefix"]
    if "dependencies" in doc:
        sort_mappings(doc["dependencies"])


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to fix")
    args = parser.parse_args(argv)
    retval = 0
    yaml = StringYAML()
    yaml.indent(mapping=4, sequence=4, offset=2)
    for filename in args.filenames:
        with open(filename, "r+") as f:
            old_contents = f.read()
            doc = yaml.load(old_contents)
            process_file(doc)
            new_contents = yaml.dump(doc)
            return
            if old_contents != new_contents:
                print(f"Fixing file `{filename}`")
                f.seek(0)
                f.write(new_contents)
                f.truncate()
                retval = 1

    return retval


if __name__ == "__main__":
    sys.exit(main())
