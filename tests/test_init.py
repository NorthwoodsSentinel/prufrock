"""Tests for prufrock/__init__.py: the package exposes its version string."""

import re

import prufrock


def test_version_is_a_dotted_string():
    assert re.fullmatch(r"\d+\.\d+\.\d+", prufrock.__version__)
