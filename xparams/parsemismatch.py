"""
Parse Mismatch
==============
"""
from enum import Enum
from typing import Optional

ParseMismatchType = Enum('ParseMismatch', ['BADKEY', 'TYPING'])


class ParseMismatch:
    def __init__(
        self,
        pm_type: ParseMismatchType,
        position: list[str],
        key: str,
        default_type: Optional[type] = None,
        toml_type: Optional[type] = None,
    ):
        self.pm_type = pm_type
        self.position = position
        self.key = key
        self.default_type = default_type.__name__ if default_type else None
        self.toml_type = toml_type.__name__ if toml_type else None

    def __str__(self):
        hierarchy = (
            f'at level: {".".join(self.position)}'
            if self.position
            else "at root level"
        )
        match self.pm_type:
            case ParseMismatchType.TYPING:
                return (
                    f'Type mismatch {hierarchy} - key: {self.key},'
                    f' default_type: {self.default_type}, toml_type:'
                    f' {self.toml_type}\n'
                )
            case ParseMismatchType.BADKEY:
                return f'Bad key {hierarchy} - key: {self.key}\n'

    def __repr__(self):
        return (
            f'ParseMismatch({self.pm_type} at'
            f' {self.position if self.position else "root"}, {self.key}, '
            + f'types: {self.default_type}, {self.toml_type})'
        )
