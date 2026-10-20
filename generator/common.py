"""Shared paths and helpers for the content generator."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MATERIALS = REPO.parent  # the "Assignment 2" course folder
DOCS = REPO / "docs"
FILES = DOCS / "files"
DATA = DOCS / "data"

EXCEL = MATERIALS / "Excel"
SQL = MATERIALS / "SQL"


def money(x):
    """Format a number as 1,234.56 (negative sign kept)."""
    return f"{x:,.2f}"


def num(x, decimals=2):
    """Format a number without trailing zeros where possible."""
    if isinstance(x, int) or float(x).is_integer():
        return f"{int(round(x)):,}"
    return f"{x:,.{decimals}f}"


class Bank:
    """Collects questions for one dataset."""

    def __init__(self, dataset, tool):
        self.dataset = dataset
        self.tool = tool
        self.items = []

    def add(self, prompt, answer, solution, minutes=1.5, skills=()):
        self.items.append({
            "tool": self.tool,
            "dataset": self.dataset,
            "prompt": prompt.strip(),
            "answer": str(answer),
            "solution": solution.strip(),
            "minutes": minutes,
            "skills": list(skills),
        })
