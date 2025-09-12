"""Testing utilities for the tiny click stub."""
from __future__ import annotations

import io
from contextlib import redirect_stdout


def _parse_args(args):
    kwargs = {}
    mapping = {
        "-t": "topics",
        "--topics": "topics",
        "-h": "hours",
        "--hours": "hours",
        "-e": "email",
        "--email": "email",
        "-r": "region",
        "--region": "region",
        "-l": "language",
        "--language": "language",
        "--maxrecords": "maxrecords",
        "-v": "verbose",
        "--verbose": "verbose",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-v", "--verbose"):
            kwargs[mapping[arg]] = True
            i += 1
        else:
            key = mapping.get(arg)
            if key:
                i += 1
                if i < len(args):
                    kwargs[key] = args[i]
            i += 1
    defaults = {
        "topics": "finance,economy,politics",
        "hours": 8,
        "email": None,
        "region": None,
        "language": None,
        "maxrecords": 75,
        "verbose": False,
    }
    for k, v in defaults.items():
        kwargs.setdefault(k, v)
    if "hours" in kwargs and isinstance(kwargs["hours"], str):
        kwargs["hours"] = int(kwargs["hours"])
    if "maxrecords" in kwargs and isinstance(kwargs["maxrecords"], str):
        kwargs["maxrecords"] = int(kwargs["maxrecords"])
    return kwargs


class CliRunner:
    def invoke(self, func, args=None):
        args = args or []
        kwargs = _parse_args(args)
        buf = io.StringIO()
        exit_code = 0
        try:
            with redirect_stdout(buf):
                func(**kwargs)
        except SystemExit as e:
            exit_code = e.code or 0
        return type("Result", (), {"exit_code": exit_code, "output": buf.getvalue()})
