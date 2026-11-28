#!/usr/bin/env bash
# A Python project whose entry points are Makefile targets.
set -euo pipefail
printf '"""Count words."""\n\n\ndef count(text):\n    return len(text.split())\n' >wordcount.py
printf 'from wordcount import count\n\n\ndef test_count():\n    assert count("a b") == 2\n' >test_wordcount.py
printf '[project]\nname = "wordcount"\nrequires-python = ">=3.10"\n' >pyproject.toml
printf '.PHONY: install test\n\n## Install dependencies\ninstall:\n\tpip install -e . pytest\n\n## Run the tests\ntest:\n\tpytest -q\n' >Makefile
