#!/usr/bin/env python

import sys
import pathlib
import subprocess
import re
from collections import Counter
import click


def _split_prefix(path, prefixes):
    if prefixes is None:
        return (None, path)
    for prefix in prefixes:
        try:
            short = path.relative_to(prefix)
            return (prefix, short)
        except ValueError:
            continue
    return (None, path)


def get_tags(files, max_tags, max_depth, prefixes=None):
    paths = [_split_prefix(pathlib.Path(f.decode()), prefixes) for f in files if f]
    for depth in reversed(range(1, max_depth + 1)):
        counts = Counter([(p[0], p[1].parent.parts[:depth]) for p in paths])
        for p in list(counts):
            if not p[1]:
                del counts[p]
        if len(counts) <= max_tags:
            break
    if not counts or len(counts) > max_tags:
        return []
    tags = ["/".join(p[1]) for p, _ in counts.most_common()]
    return tags


@click.command()
@click.option(
    "-p",
    "--prefix",
    help="Path prefix to strip from beginning of file paths.",
    multiple=True,
)
@click.option(
    "-d",
    "--depth",
    help="Maximum number of path components to include in tags.",
    default=2,
)
@click.option("-t", "--tags", help="Maximum number of tags.", default=2)
@click.argument("commit_msg_file")
def cli(commit_msg_file, prefix, depth, tags):
    prefix = [pathlib.Path(p) for p in prefix]
    ret = subprocess.run(
        ["git", "diff-index", "-z", "--cached", "HEAD", "--name-only"],
        capture_output=True,
    )

    if ret.returncode != 0:
        sys.exit(ret.returncode)

    changed_files = ret.stdout.split(b"\x00")
    new_tags = get_tags(changed_files, tags, depth, prefixes=prefix)

    with open(commit_msg_file, "r+") as f:
        full_msg = f.read()
        match = re.match(r"^\s*\[([^\]]+)\]\s*(.*)", full_msg)
        if match:
            old_tags = match.group(1).split(",")
            old_msg = match.group(2)
        else:
            old_tags = []
            old_msg = full_msg
        tags = list(set(old_tags) + set(new_tags))
        if not tags:
            sys.exit(0)
        tag_str = f"[{','.join(tags)}]"
        f.seek(0)
        new_msg = tag_str + " " + old_msg
        f.write(new_msg)


if __name__ == "__main__":
    cli()
