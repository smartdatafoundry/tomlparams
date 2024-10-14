"""captureoutput.py.

Copyright (c) Stochastic Solutions Limited 2016-2023

MIT Licensed.
"""

import sys


class CaptureOutput(object):
    """Class for capturing a stream (typically) stdout.

    Typical Usage:

        c = CaptureOutput()  # for stdout; add stream='stderr' for stderr.
        try:
            <do stuff>
        finally:
            c.restore()
        printed = str(c)
    """

    def __init__(self, echo: bool = False, stream: str = "stdout") -> None:
        self.stream = stream
        if stream == "stdout":
            self.saved = sys.stdout
            sys.stdout = self
        elif stream == "stderr":
            self.saved = sys.stderr
            sys.stderr = self
        else:
            raise Exception("Unsupported capture stream %s" % stream)
        self.out: list[str] = []
        self.echo: bool = echo

    def write(self, s: str) -> None:
        self.out.append(s)
        if self.echo:
            self.saved.write(s)

    def flush(self) -> None:
        if self.echo:
            self.saved.flush()

    def getvalue(self) -> None:
        self.saved.flush()

    def restore(self) -> None:
        if self.stream == "stdout":
            sys.stdout = self.saved
        else:
            sys.stderr = self.saved

    def __str__(self) -> str:
        return "".join(self.out)
