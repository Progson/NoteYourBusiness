# tests/test_walker_exclusions.py
from pathlib import Path
from nyb.core import walker

def test_walker_basic(tmp_path: Path):
    # Struktura: root / a.txt, b.nyb, sub/ c.txt
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.nyb").write_text("b")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.txt").write_text("c")

    paths = [str(tmp_path)]
    results = list(walker.iter_targets(paths, recursive=True, exclusions=["does-not-match"]))
    files = {p.path.name for p in results if p.kind == "file"}
    # walker zwraca wszystkie pliki; filtr .nyb zastosujemy w io
    assert "a.txt" in files
    assert "b.nyb" in files
    assert "c.txt" in files
