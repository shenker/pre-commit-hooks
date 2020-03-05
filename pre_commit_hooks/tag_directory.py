#!/usr/bin/env python

import sys
import pathlib
import subprocess
from collections import Counter
import click


def _split_prefix(path, prefixes):
    if prefixes is None:
        return (None, path)
    for prefix in prefixes:
        try:
            short = path.relative_to(prefix)
            return short
        except ValueError:
            continue
    return (None, path)


def get_tags(files, max_tags, max_depth, prefixes=None):
    paths = [_split_prefix(pathlib.Path(f.decode()), prefixes) for f in files if f]
    for depth in reversed(range(1, max_depth + 1)):
        counts = Counter([(p[0], p[1].parent.parts[:depth]) for p in paths])
        del counts[()]
        if len(counts) <= max_tags:
            break
    if not counts or len(counts) > max_tags:
        return None
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
    tags = get_tags(changed_files, tags, depth, prefixes=prefix)
    if tags is None:
        sys.exit(0)
    tag_str = f"[{','.join(tags)}]"

    with open(commit_msg_file, "r+") as f:
        msg = f.read()
        f.seek(0)
        f.write(tag_str + " " + msg)


if __name__ == "__main__":
    cli()
