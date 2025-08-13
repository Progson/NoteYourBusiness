import argparse
import sys
from nyb.app import run_gui

def parse_args(argv):
    p = argparse.ArgumentParser(prog="nyb", description="NoteYourBusiness")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--encrypt", nargs="+", help="Szyfruj pliki/foldery")
    g.add_argument("--decrypt", nargs="+", help="Odszyfruj pliki .nyb")
    g.add_argument("--edit", help="Otwórz edytor notatki .nybnote")
    p.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--replace-original", action="store_true")
    p.add_argument("--keep-original", action="store_true")
    p.add_argument("--keep-nyb", action="store_true")
    p.add_argument("--remove-nyb", action="store_true")
    p.add_argument("--password", help="PROMPT lub ENV:NYB_PASS")
    p.add_argument("--json-log", help="Ścieżka do logu JSON")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)

def run_cli(ns) -> int:
    # TODO: wywołanie core.* w zależności od trybu + raportowanie kodów wyjścia
    if not any([ns.encrypt, ns.decrypt, ns.edit]):
        run_gui()
        return 0
    print("[NYB] CLI skeleton – tu wywołamy operacje encrypt/decrypt/edit.")
    return 0

def main() -> int:
    ns = parse_args(sys.argv[1:])
    return run_cli(ns)

if __name__ == "__main__":
    raise SystemExit(main())
