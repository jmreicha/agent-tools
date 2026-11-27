#!/usr/bin/env bash
# A repo that already runs tests from a scripts/ dir: new entry points must follow it.
set -euo pipefail
mkdir -p scripts
cat >scripts/test.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
pytest -q
SH
chmod +x scripts/test.sh
cat >wordfreq.py <<'PY'
"""Count word frequencies in a file, minus stop words."""
import argparse
import collections
import sys

STOP = {"the", "a", "an", "and", "or", "of", "to", "in"}


def counts(text):
    words = [w.strip(".,!?;:").lower() for w in text.split()]
    words = [w for w in words if w and w not in STOP]
    return collections.Counter(words)


def main(argv=None):
    p = argparse.ArgumentParser(prog="wordfreq", description=__doc__)
    p.add_argument("file", help="File to read, or - for stdin")
    args = p.parse_args(argv)
    text = sys.stdin.read() if args.file == "-" else open(args.file).read()
    for word, n in counts(text).most_common():
        print(f"{n} {word}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
cat >test_wordfreq.py <<'PY'
from wordfreq import counts


def test_counts_ignores_stop_words():
    assert counts("the cat and the dog") == {"cat": 1, "dog": 1}


def test_counts_are_case_insensitive():
    assert counts("Cat CAT") == {"cat": 2}
PY
printf 'requires-python = ">=3.10"\n' >pyproject.toml
