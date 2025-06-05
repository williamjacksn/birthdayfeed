import json
import pathlib


def gen(content: dict, target: pathlib.Path):
    target.write_text(json.dumps(content, indent=2, sort_keys=True), newline="\n")
