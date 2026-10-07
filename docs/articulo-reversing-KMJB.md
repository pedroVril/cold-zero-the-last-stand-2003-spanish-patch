# Cómo se rompió el cifrado de textos de ColdZero — paso a paso

Artículo teórico del proceso de ingeniería inversa. Cualquiera con las mismas
herramientas puede recrearlo siguiendo estos pasos.

## 1. El síntoma: textos que no aparecen por ningún lado

El objetivo era traducir el juego del inglés al español. Al abrir la carpeta del juego
(`C:\Program Files (x86)\JoWooD\ColdZero`) no había ningún `.ini` ni `.txt` con los
diálogos o menús. Solo archivos `.cdi` (en `Settings\`) y `.cdt`/`.cdm` (en `Data\`),
ilegibles al abrirlos con un editor: bytes aparentemente aleatorios.

Hipótesis: los textos están cifrados o comprimidos en un formato propio.

## 2. Medir antes de suponer: magic + entropía

En vez de adivinar, se midieron dos cosas en cada archivo con un script Python
(como este, simplificado):

```py
import math, os
from collections import Counter

def entropia(data: bytes) -> float:
    n = len(data)
    return -sum((v / n) * math.log2(v / n) for v in Counter(data).values())

for f in sorted(os.listdir("Settings")):
    p = os.path.join("Settings", f)
    d = open(p, "rb").read()
    print(f"{f:20} magic={d[:4]!r} entropia={entropia(d):.2f}")
# GameTexts.cdi  magic=b'KMJB' entropia=7.82  -> cifrado
# Assets.bin     magic=b'\x01\x00La' entropia=1.28  -> texto plano
```

1. **Magic** (primeros bytes): todos los `.cdi`/`.cdt` empiezan por `KMJB`
   (`4B 4D 4A 42`). Los niveles `.LV2`, mapas y modelos empiezan por `DE ZLock1`.
2. **Entropía** (0–8 bits/byte, mide aleatoriedad):
   - `GameTexts.cdi`: 7.82; resto de `.cdi`/`.cdt`: 7.3–7.8 → ruido, típico de cifrado.
   - `Assets.bin`: 1.28 → y efectivamente contiene inglés legible (armas/items).
   - Un texto inglés normal ronda 4.5. Un 7.8 confirma que no es texto plano.

Conclusión provisional: UI, menús, diálogos y misiones están codificados; solo
`Assets.bin` es traducible directamente.

## 3. Pistas dentro del ejecutable

Buscando strings en `ColdZero.exe` aparecieron las piezas clave, juntas
(script simplificado):

```py
import re
exe = open("ColdZero.exe", "rb").read()
strs = re.findall(rb"[ -~]{6,}", exe)          # strings ASCII de 6+ letras
for s in strs:
    if b"KMJB" in s or b"decoding" in s or s.endswith(b".ini"):
        print(s[:100])
# KMJB ... ERROR : Ini decoding FAILURE ! ... Settings\GameTexts.ini ...
```

- `KMJB` y `DE ZLock1` (los mismos magics),
- `ERROR : Ini decoding FAILURE !` y `Win/Coded values : %d/%d`,
- 91 referencias a `Settings\*.ini` (`GameTexts.ini`, `Dialog.ini`, `MOptions.ini`…),
  **pero en disco esos archivos existen como `.cdi`**.

Deducción: el juego pide `.ini` en claro, el lector propio los lee como `.cdi`
codificados, y compara ambos (de ahí el mensaje de error si difieren).
El `.cdi` es, por tanto, un **`.ini` codificado**, y el decodificador vive en el `.exe`.

## 4. Montar el laboratorio: Ghidra + MCP

Para leer el `.exe` se instaló Ghidra 12.1.3 (`C:\Ghidra`) con la extensión
[ghidra-mcp](https://github.com/bethington/ghidra-mcp) (v7.0.0), que expone el
análisis como servidor HTTP local (`127.0.0.1:8089`). Pasos:

1. `git clone` del repo, `preflight`, `ensure-prereqs`, `build`, `deploy`
   (backend Gradle, variable `GHIDRA_INSTALL_DIR=C:\Ghidra` obligatoria para compilar).
2. Abrir Ghidra, crear proyecto, importar `ColdZero.exe` y dejarlo abierto.
3. Verificar salud: `GET /mcp/instance_info` → `200`, 205 endpoints, programa abierto.

## 5. Cazar la rutina: del string al algoritmo

Con el servidor MCP, siguiendo los hilos (todo por HTTP, ejemplo simplificado):

```py
import urllib.request, urllib.parse, json
base = "http://127.0.0.1:8089"

def get(path, **q):
    url = base + path + "?" + urllib.parse.urlencode(q)
    return json.loads(urllib.request.urlopen(url, timeout=60).read())

def post(path, **body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

# 1. ¿Dónde se usa el mensaje de error?
hits = get("/search_strings", search_term="Ini decoding")
# -> 5 direcciones, ej. 005174a4

# 2. ¿Qué función lo usa?
print(get("/get_xrefs_to", address="005174a4"))
# -> [{"from_address": "004dcbf9", "from_function": "FUN_004dcb15"}]

# 3. Descompilar la candidata y seguir la cadena hacia abajo
print(post("/force_decompile", function="004dcb15"))
# -> llama a GetPrivateProfileStringA Y a FUN_004dd250, y compara: envoltorio
# -> FUN_004dd250 -> FUN_004dd6e7 (CreateFileA/ReadFile + chequeo KMJB/AACL)
# -> FUN_004dd99b: DWORD[i] ^= key; key = ROL32(key, 1), key = 0xA8C15E3D
```

El "cifrado" resultó ser un XOR con rotación de 1 bit por DWORD. Sin compresión
(`zlib` ya había fallado antes, pista de que era cifrado puro).

## 6. Confirmación empírica: descifrar de verdad

Se reimplementó en Python (`herramientas/kmjb.py`): saltar 4 bytes de magic, XOR
por DWORDs little-endian con la key rotando. El núcleo, literalmente:

```py
def rol32(v: int) -> int:
    return ((v << 1) & 0xFFFFFFFF) | (v >> 31)

def crypt(data: bytes, key: int = 0xA8C15E3D) -> bytes:
    out = bytearray(data)
    for i in range(0, len(out), 4):
        n = min(4, len(out) - i)
        val = int.from_bytes(out[i:i + 4], "little") ^ key
        out[i:i + n] = val.to_bytes(4, "little")[:n]
        key = rol32(key)
    return bytes(out)

plain = crypt(open("GameTexts.cdi", "rb").read()[4:])
# b"[main]\r\nFasttextsFontId = 4\r\n..."  -> un .ini perfecto
```

Al aplicarlo a `GameTexts.cdi` salió un `.ini` perfecto.

Prueba de fuego (**round-trip**): descifrar y volver a cifrar los 250 archivos
(`Settings` + `Data`, con subcarpetas) reproduce los originales **byte por byte**
(208/208 y 42/42, cero fallos). Como el XOR es simétrico, codificar = decodificar,
y el juego aceptará archivos regenerados.

## 7. Extracción y organización para traducir

- `kmjb.py batch` descifró todo a `originales/` (`.cdi→.ini`, `.cdt→.txt`, `.cdm→.map`):
  250 archivos, ~27.700 líneas, diálogos incluidos (`LEV_TUTORIAL.txt`).
- `espanol/` es copia de trabajo; `originales/` queda intacto como respaldo.
- Flujo de parche: traducir en `espanol/` → `build_parche.py` → probar en el juego
  con copia de seguridad. Piloto superado con el tutorial; luego juego completo.

## 8. Cómo recrearlo (resumen de herramientas)

- Python 3.14 + Ghidra 12.1.3 + JDK 21 + `uv` + repo `bethington/ghidra-mcp` (rama `dev`).
- Scripts propios: medición de entropía/magics, `herramientas/kmjb.py`.
- Endpoints MCP usados: `/mcp/instance_info`, `/mcp/schema`, `/search_strings`,
  `/get_xrefs_to`, `/force_decompile`, `/read_memory`.
- Punto de entrada al reversing: el string `Ini decoding` (ancla mucho mejor que
  empezar a ciegas por el `main`).

## 9. Límites conocidos

- Magic `AACL` (key `0xDAC1A666`): mismo esquema, otro tipo de archivo; aún sin
  muestras en el juego instalado.
- `DE ZLock1` (niveles, texturas, modelos): formato distinto, sin texto traducible
  a la vista; pendiente si hiciera falta.
- Los `.cdt` regenerados fueron aceptados por el juego sin avisos
  (`Ini decoding FAILURE` no aparece) y los textos se muestran correctamente.
