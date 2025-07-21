"""Git operations package for handling repository interactions."""

from .differ import GitDiffer
from .parser import DiffParser
from .files import FileHandler

__all__ = [
    "GitDiffer",
    "DiffParser", 
    "FileHandler",
] 