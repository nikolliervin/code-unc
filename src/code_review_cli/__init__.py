"""
Code Review CLI - AI-powered code review tool.

A command-line tool that fetches git diff between branches and uses AI
to provide CodeRabbit-style code reviews.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .cli.main import app

__all__ = ["app"] 