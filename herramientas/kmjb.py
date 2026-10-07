"""KMJB coded-INI codec — ColdZero (JoWooD, 2003).

Reversing: ColdZero.exe FUN_004dd6e7 (loader) + FUN_004dd99b (decoder).
  - Si los 4 primeros bytes son b'KMJB', el resto del archivo son DWORDs little-endian
    con XOR encadenado: key inicial 0xA8C15E3D, rotación izquierda de 1 bit por DWORD.
  - Magic alternativo b'AACL' -> key 0xDAC1A666 (mismo esquema, otro tipo de archivo).
  - El decode cubre desde el offset 4 hasta EOF (último DWORD parcial incluido).
  - XOR es simétrico: codificar == decodificar. Round-trip verificado byte a byte.

Uso:
  python kmjb.py decode <origen.cdi> <destino.ini>
  python kmjb.py encode <origen.ini> <destino.cdi> [--magic KMJB]
  python kmjb.py batch <carpeta_origen> <carpeta_destino>   # decode masivo
  python kmjb.py roundtrip <carpeta>                        # verifica todos los .cdi/.cdt/.cdm
"""
import struct
import sys
from pathlib import Path

MAGICS = {b"KMJB": 0xA8C15E3D, b"AACL": 0xDAC1A666}
# Extensión descodificada según tipo (el juego mapea ini->cdi, txt->cdt, map->cdm)
DECODED_EXT = {".cdi": ".ini", ".cdt": ".txt", ".cdm": ".map"}
CODED_EXT = {v: k for k, v in DECODED_EXT.items()}


def rol32(v: int, n: int = 1) -> int:
    return ((v << n) & 0xFFFFFFFF) | (v >> (32 - n))


def crypt(data: bytes, key: int) -> bytes:
    out = bytearray(data)
    for i in range(0, len(out), 4):
        n = min(4, len(out) - i)
        val = int.from_bytes(out[i:i + 4], "little") ^ key
        out[i:i + n] = val.to_bytes(4, "little")[:n]
        key = rol32(key, 1)
    return bytes(out)


def decode_file(src: Path) -> tuple[bytes, bytes]:
    raw = src.read_bytes()
    magic, body = raw[:4], raw[4:]
    if magic not in MAGICS:
        raise ValueError(f"{src}: magic desconocido {magic!r}")
    return magic, crypt(body, MAGICS[magic])


def encode_file(src: Path, magic: bytes = b"KMJB") -> bytes:
    return magic + crypt(src.read_bytes(), MAGICS[magic])


def cmd_decode(src: str, dst: str) -> None:
    magic, plain = decode_file(Path(src))
    Path(dst).write_bytes(plain)
    print(f"{src} [{magic.decode()}] -> {dst} ({len(plain)} bytes)")


def cmd_encode(src: str, dst: str, magic: bytes = b"KMJB") -> None:
    Path(dst).write_bytes(encode_file(Path(src), magic))
    print(f"{src} -> {dst} [{magic.decode()}]")


def cmd_batch(src_dir: str, dst_dir: str) -> None:
    src_dir, dst_dir = Path(src_dir), Path(dst_dir)
    n = 0
    for f in sorted(src_dir.rglob("*")):
        if f.is_file() and f.suffix.lower() in DECODED_EXT:
            try:
                magic, plain = decode_file(f)
            except ValueError as e:
                print(f"  SKIP: {e}")
                continue
            rel = f.relative_to(src_dir)
            out = dst_dir / rel.parent / (rel.stem + DECODED_EXT[f.suffix.lower()])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(plain)
            n += 1
    print(f"Decodificados: {n}")


def cmd_roundtrip(src_dir: str) -> None:
    ok, fail = 0, []
    for f in sorted(Path(src_dir).rglob("*")):
        if f.is_file() and f.suffix.lower() in DECODED_EXT:
            raw = f.read_bytes()
            magic, plain = decode_file(f)
            if magic + crypt(plain, MAGICS[magic]) == raw:
                ok += 1
            else:
                fail.append(str(f))
    print(f"Round-trip OK: {ok}, FALLIDOS: {len(fail)}")
    for x in fail:
        print(f"  FAIL: {x}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "decode":
        cmd_decode(sys.argv[2], sys.argv[3])
    elif cmd == "encode":
        m = sys.argv[4].encode() if len(sys.argv) > 4 else b"KMJB"
        cmd_encode(sys.argv[2], sys.argv[3], m)
    elif cmd == "batch":
        cmd_batch(sys.argv[2], sys.argv[3])
    elif cmd == "roundtrip":
        cmd_roundtrip(sys.argv[2])
    else:
        sys.exit(f"comando desconocido: {cmd}")
