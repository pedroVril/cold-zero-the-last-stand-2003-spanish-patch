"""Genera el parche jugable desde espanol/.

- espanol/ son másters UTF-8 con español correcto (con acentos).
- Las líneas SIN traducir (idénticas al original) se copian byte a byte
  (conserva ruso en cp1251, comentarios polacos, etc.).
- Las líneas traducidas se normalizan al set del juego y se codifican
  en cp1252 (1 byte/letra; el juego lee byte a byte, UTF-8 lo corrompe).
- Codifica .ini->.cdi, .txt->.cdt, .map->.cdm con magic KMJB y verifica.

Uso:
  python build_parche.py              # todo espanol/ -> parche/
"""
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
ESP = BASE / "espanol"
ORIG = BASE / "originales"
OUT = BASE / "parche"

sys.path.insert(0, str(AQUI))
from kmjb import crypt, MAGICS  # noqa: E402

# Válidos en el juego (sonda 2026-10-06): vocales acentuadas + diéresis.
VALIDOS = set("áéíóúÁÉÍÓÚüÜ")
# Inválidos confirmados (ñ Ñ ¡ ¿) y tipográficos -> sustituto seguro.
EXTRA = {"¡": "!", "¿": "?", "«": '"', "»": '"', "“": '"', "”": '"',
         "‘": "'", "’": "'", "–": "-", "—": "-", "…": "...", "·": "-",
         "ñ": "n", "Ñ": "N"}
CODED_EXT = {".ini": ".cdi", ".txt": ".cdt", ".map": ".cdm"}


def normalizar(texto: str) -> str:
    out = []
    for ch in texto:
        if ch in EXTRA:
            out.append(EXTRA[ch])
            continue
        if ch in VALIDOS or ch.isascii():
            out.append(ch)
            continue
        base = unicodedata.normalize("NFKD", ch)
        base = "".join(c for c in base if not unicodedata.combining(c))
        out.append(base if len(base) == 1 and base.isascii() else "")
    return "".join(out)


def build_file(es_path: Path, orig_path: Path, dst_path: Path) -> None:
    es_lines = es_path.read_bytes().split(b"\n")
    og_lines = orig_path.read_bytes().split(b"\n") if orig_path.exists() else []
    out_lines = []
    for i, el in enumerate(es_lines):
        try:
            el.decode("utf-8")  # los másters traducidos son UTF-8 válido
            es_texto = True
        except UnicodeDecodeError:
            es_texto = False
        if not es_texto:
            out_lines.append(el)  # bytes originales (ruso, etc.): byte a byte
        elif i < len(og_lines) and el == og_lines[i]:
            out_lines.append(el)  # sin tocar: byte a byte
        else:
            norm = normalizar(el.decode("utf-8", errors="replace"))
            try:
                out_lines.append(norm.encode("cp1252"))
            except UnicodeEncodeError:
                raise ValueError(f"{es_path}:{i + 1} caracter fuera de cp1252: {norm!r}")
    raw = b"\n".join(out_lines)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_bytes(b"KMJB" + crypt(raw, MAGICS[b"KMJB"]))
    assert crypt(dst_path.read_bytes()[4:], MAGICS[b"KMJB"]) == raw, es_path


def build() -> None:
    n = 0
    for f in sorted(ESP.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in CODED_EXT:
            continue
        rel = f.relative_to(ESP)
        dst = OUT / rel.parent / (rel.stem + CODED_EXT[f.suffix.lower()])
        build_file(f, ORIG / rel, dst)
        n += 1
    leeme = BASE / "LEEME.txt"
    if leeme.exists():
        import shutil
        shutil.copy(leeme, OUT / "LEEME.txt")
        print("LEEME.txt incluido en el parche")
    print(f"Parche generado: {n} archivos en {OUT}")


if __name__ == "__main__":
    build()
