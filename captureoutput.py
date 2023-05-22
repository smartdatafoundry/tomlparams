"""
captureoutput.py

Copyright (c) Stochastic Solutions Limited 2016-2023

MIT Licensed.
"""

import sys


class CaptureOutput(object):
    """
    Class for capturing a stream (typically) stdout.

    Typical Usage:

        c = CaptureOutput()  # for stdout; add stream='stderr' for stderr.
        try:
            <do stuff>
        finally:
            c.restore()
        printed = str(c)
    """

    def __init__(self, echo=False, stream="stdout"):
        self.stream = stream
        if stream == "stdout":
            self.saved = sys.stdout
            sys.stdout = self
        elif stream == "stderr":
            self.saved = sys.stderr
            sys.stderr = self
        else:
            raise Exception("Unsupported capture stream %s" % stream)
        self.out = []
        self.echo = echo

    def write(self, s):
        self.out.append(s)
        if self.echo:
            self.saved.write(s)

    def flush(self):
        if self.echo:
            self.saved.flush()

    def getvalue(self):
        self.saved.flush()

    def restore(self):
        if self.stream == "stdout":
            sys.stdout = self.saved
        else:
            sys.stderr = self.saved

    def __str__(self):
        return "".join(self.out)
