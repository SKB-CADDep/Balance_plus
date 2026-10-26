from types import SimpleNamespace

import pandas as pd

from app.scripts.load_condensers import load_condensers, resolve_main_count


MAIN_COUNT_COLUMN = "Количество_охлаждающих_труб_основного_пучка_шт"
TOTAL_COUNT_COLUMN = "Общее_количество_охлаждающих_труб_шт"


def test_resolve_main_count_keeps_explicit_bundle_value() -> None:
    row = pd.Series({MAIN_COUNT_COLUMN: 1200, TOTAL_COUNT_COLUMN: 3000})

    assert resolve_main_count(row) == 1200


def test_resolve_main_count_uses_total_when_bundle_value_is_zero() -> None:
    row = pd.Series({MAIN_COUNT_COLUMN: 0, TOTAL_COUNT_COLUMN: 3012})

    assert resolve_main_count(row) == 3012


def test_resolve_main_count_uses_total_when_bundle_value_is_empty() -> None:
    row = pd.Series({MAIN_COUNT_COLUMN: None, TOTAL_COUNT_COLUMN: 3804})

    assert resolve_main_count(row) == 3804


def test_resolve_main_count_does_not_hide_invalid_negative_value() -> None:
    row = pd.Series({MAIN_COUNT_COLUMN: -1, TOTAL_COUNT_COLUMN: 3804})

    assert resolve_main_count(row) == -1


class _ExistingCondenserQuery:
    def __init__(self, condenser) -> None:
        self.condenser = condenser

    def filter(self, *_args):
        return self

    def first(self):
        return self.condenser


class _ExistingCondenserSession:
    def __init__(self, condenser) -> None:
        self.condenser = condenser
        self.committed = False

    def query(self, _model):
        return _ExistingCondenserQuery(self.condenser)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        raise AssertionError("rollback не должен вызываться")


def test_load_condensers_repairs_existing_zero_main_count(
    monkeypatch, tmp_path
) -> None:
    existing = SimpleNamespace(main_count=0)
    session = _ExistingCondenserSession(existing)
    source = tmp_path / "condensers.xlsx"
    source.touch()
    dataframe = pd.DataFrame(
        [
            {
                "Тип_конденсатора": "К-740-1",
                MAIN_COUNT_COLUMN: 0,
                TOTAL_COUNT_COLUMN: 3012,
            }
        ]
    )
    monkeypatch.setattr(pd, "read_excel", lambda _path: dataframe)

    load_condensers(session, str(source))

    assert existing.main_count == 3012
    assert session.committed is True
