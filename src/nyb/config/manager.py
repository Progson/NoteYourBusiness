from pathlib import Path
import json, os

APP_DIR = Path(os.getenv('APPDATA', '.')) / 'NoteYourBusiness'
CFG_PATH = APP_DIR / 'config.json'

DEFAULTS = {
  "defaults": {"recursive": True, "replace_original": False, "remove_nyb_after_decrypt": True, "send_to_recycle_bin": True},
  "argon2": {"m": 134217728, "t": 3, "p": 1},
  "exclusions": ["$Recycle.Bin", "System Volume Information", "Windows\\Temp"],
  "io": {"chunk_size": 4194304, "max_parallel_kdf": 1}
}

def get_config_path() -> Path: return CFG_PATH

def load_config() -> dict:
    try:
        return json.loads(CFG_PATH.read_text(encoding='utf-8'))
    except FileNotFoundError:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        save_config(DEFAULTS)
        return DEFAULTS.copy()

def save_config(cfg: dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
