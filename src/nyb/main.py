# src/nyb/main.py
import argparse
import os
import sys
from getpass import getpass
from pathlib import Path

from nyb.app import run_gui
from nyb.config import manager as cfgman
from nyb.core import io as nybio
from nyb.core import walker

def parse_args(argv):
    p = argparse.ArgumentParser(prog="nyb", description="NoteYourBusiness")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--encrypt", nargs="+", metavar="PATH", help="Szyfruj pliki/foldery")
    g.add_argument("--decrypt", nargs="+", metavar="PATH", help="Odszyfruj pliki/foldery (.nyb)")
    g.add_argument("--edit", help="Otwórz edytor notatki .nybnote (stub)")
    p.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
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
    return lambda: getpass("Hasło: ").encode("utf-8")

def _print_status(ok: bool, action: str, src: Path, out: str):
    if ok:
        print(f"[OK] {action}: {src} -> {out}")
    else:
        print(f"[SKIP] {action}: {src}")

def run_cli(ns) -> int:
    if not any([ns.encrypt, ns.decrypt, ns.edit]):
        run_gui()
        return 0

    cfg = cfgman.load_config()
    pw = _password_resolver(ns.password)
    exclusions = cfg.get("exclusions", ["$Recycle.Bin", "System Volume Information", "Windows\\Temp"])

    try:
        if ns.encrypt:
            any_error = False
            for task in walker.iter_targets(ns.encrypt, ns.recursive, exclusions):
                if task.kind == "file":
                    if ns.dry_run:
                        _print_status(True, "ENCRYPT (dry-run)", task.path, str(task.path) + ".nyb")
                        continue
                    out = nybio.encrypt_file(task.path, pw, cfg)
                    _print_status(bool(out), "ENCRYPT", task.path, out)
                # katalogi obsługuje walker (nie wywołujemy encrypt na dir)
            return 0 if not any_error else 1

        if ns.decrypt:
            any_error = False
            for task in walker.iter_targets(ns.decrypt, ns.recursive, exclusions):
                if task.kind == "file" and task.path.suffix.lower() == ".nyb":
                    if ns.dry_run:
                        _print_status(True, "DECRYPT (dry-run)", task.path, task.path.with_suffix(""))
                        continue
                    out = nybio.decrypt_file(task.path, pw, cfg)
                    _print_status(bool(out), "DECRYPT", task.path, out)
            return 0 if not any_error else 1

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
