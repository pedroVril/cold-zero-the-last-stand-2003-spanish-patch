# Herramientas del parche

## `build_parche.py` — generar el parche (flujo normal)

```
python build_parche.py
```

- Lee: `espanol/` (traducción) + `originales/` (inglés descifrado).
- Crea: `parche/Settings/*.cdi`, `parche/Data/*.cdt`, `parche/Data/*.cdm`
  + copia `LEEME.txt` dentro.
- No pide nada más. Cada archivo se verifica tras generarlo.

## `kmjb.py` — codec del formato KMJB (flujo "otra versión" / depuración)

Solo hace falta si partes de archivos distintos a los incluidos
(ej. otra versión del juego) o quieres inspeccionar un archivo suelto.
Necesita los archivos **originales del juego instalado**, por ejemplo:

```
C:\Program Files (x86)\JoWooD\ColdZero\Settings\   (*.cdi)
C:\Program Files (x86)\JoWooD\ColdZero\Data\       (*.cdt, *.cdm)
```

Comandos (se ejecutan desde esta carpeta `herramientas/`):

```
# Descifrar UN archivo (ver su texto en claro)
python kmjb.py decode  C:\...\ColdZero\Settings\GameTexts.cdi  GameTexts.ini

# Cifrar UN archivo suelto (.ini->.cdi, .txt->.cdt, .map->.cdm, magic KMJB)
python kmjb.py encode  MiTexto.ini  MiTexto.cdi

# Descifrar TODOS los de una carpeta (así nació originales/)
python kmjb.py batch  C:\...\ColdZero\Settings  C:\salida\Settings
python kmjb.py batch  C:\...\ColdZero\Data      C:\salida\Data
# (.cdi sale como .ini, .cdt como .txt, .cdm como .map)

# Verificar que descifrar→cifrar reproduce los originales byte a byte
python kmjb.py roundtrip  C:\...\ColdZero\Settings
python kmjb.py roundtrip  C:\...\ColdZero\Data
```

## Resumen de flujos

- **Normal (este repo, v1.02 UK):** editar `espanol/` → `python build_parche.py`.
- **Otra versión del juego:** `kmjb.py batch` sobre tu `Settings/` y `Data/`
  → esos son tus nuevos `originales/` → traducir en `espanol/` → `build_parche.py`.
