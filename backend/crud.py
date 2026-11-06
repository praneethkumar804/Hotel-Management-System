from collections.abc import Iterable
import sqlite3


def rows_as_dicts(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def row_as_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None