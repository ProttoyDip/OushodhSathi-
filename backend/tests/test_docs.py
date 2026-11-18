"""The generated reference docs must match the code: docs/API.md (the routes) and docs/CONFIGURATION.md
(backend/.env.example). Run `python backend/scripts/gen_docs.py` after changing either."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _gen():
    spec = importlib.util.spec_from_file_location("gen_docs", ROOT / "backend" / "scripts" / "gen_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_api_and_configuration_docs_are_current():
    gen = _gen()
    for path, text in ((gen.API_MD, gen.api_md()), (gen.CONFIG_MD, gen.config_md())):
        assert path.read_text(encoding="utf-8").replace("\r\n", "\n") == text, \
            f"{path.name} is out of date: run python backend/scripts/gen_docs.py"


def test_every_setting_in_env_example_is_documented():
    gen = _gen()
    doc = gen.CONFIG_MD.read_text(encoding="utf-8")
    names = [n for n, _, _ in gen._env_rows()]
    assert names and all(f"`{n}`" in doc for n in names)
