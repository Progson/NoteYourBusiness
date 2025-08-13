# src/nyb/main.py
import argparse
import os
import sys
from getpass import getpass

from nyb.app import run_gui
from nyb.config import manager as cfgman
from nyb.core import io as nybio

def parse_args(argv):
    p = argparse.ArgumentParser(prog="nyb", description="NoteYourBusiness")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--encrypt", help="Szyfruj plik (minimalna wersja)", metavar="PATH")
    g.add_argument("--decrypt", help="Odszyfruj plik .nyb (minimalna wersja)", metavar="FILE.nyb")
    g.add_argument("--edit", help="Otwórz edytor notatki .nybnote (stub)", metavar="FILE.nybnote")
    p.add_argument("--password", help="PROMPT lub ENV:NYB_PASS")
    p.add_argument("--json-log", help="Ścieżka do logu JSON")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)

def _password_resolver(opt: str | None):
    if opt and opt.upper().startswith("ENV:"):
        envname = opt.split(":", 1)[1]
        pw = os.getenv(envname, "")
        return lambda: pw.encode("utf-8")
    if opt and opt.upper() == "PROMPT":
        return lambda: getpass("Hasło: ").encode("utf-8")
    if opt:  # literal
        return lambda: opt.encode("utf-8")
    # default: prompt
    return lambda: getpass("Hasło: ").encode("utf-8")

def run_cli(ns) -> int:
    if not any([ns.encrypt, ns.decrypt, ns.edit]):
        run_gui()
        return 0

    cfg = cfgman.load_config()
    pw = _password_resolver(ns.password)

    try:
        if ns.encrypt:
            out = nybio.encrypt_path(ns.encrypt, pw, cfg)
            print(f"[OK] Zaszyfrowano → {out}")
            return 0
        if ns.decrypt:
            out = nybio.decrypt_path(ns.decrypt, pw, cfg)
            print(f"[OK] Odszyfrowano → {out}")
            return 0
        if ns.edit:
            print("[INFO] Edytor notatek jeszcze niezaimplementowany w CLI.")
            return 0
    except Exception as e:
        print(f"[ERROR] {e}")
        return 2

def main() -> int:
    ns = parse_args(sys.argv[1:])
    return run_cli(ns)

if __name__ == "__main__":
    raise SystemExit(main())
