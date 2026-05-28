"""Shared helper: parse a draft markdown file with YAML frontmatter."""
import pathlib
import re
import yaml

_FM = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def parse(md_path) -> tuple[dict, str]:
    """Return (metadata dict, markdown body) from a draft file.

    The file must start with a YAML frontmatter block delimited by --- lines.
    """
    text = pathlib.Path(md_path).read_text()
    m = _FM.match(text)
    if not m:
        raise SystemExit(
            f"{md_path}: missing YAML frontmatter (a block between --- lines at the top)."
        )
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    required = ["title"]
    missing = [k for k in required if not meta.get(k)]
    if missing:
        raise SystemExit(f"{md_path}: frontmatter missing required keys: {missing}")
    return meta, body
