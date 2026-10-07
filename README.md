# Cold Zero — Parche de traducción al español

Traducción al español de los textos del juego **ColdZero** (JoWooD, 2003):
menús, tutorial, 16 niveles, objetivos, habilidades, tiendas y multijugador.

![Cold Zero](images/coldzero-front.png)

## Índice

- [Cold Zero — Parche de traducción al español](#cold-zero--parche-de-traducción-al-español)
  - [Índice](#índice)
  - [Versión del juego](#versión-del-juego)
  - [Qué hay en cada carpeta](#qué-hay-en-cada-carpeta)
  - [Herramientas](#herramientas)
  - [Generar el parche](#generar-el-parche)
  - [Instalar el parche](#instalar-el-parche)
  - [Mejorar la traducción](#mejorar-la-traducción)

## Versión del juego

Probado sobre la **versión 1.02 UK** (texto `1.02` presente en `ColdZero.exe`).
En otras versiones o regiones los archivos `.cdi`/`.cdt` podrían diferir: ante
la duda, regenerar `originales/` desde los archivos propios con `kmjb.py batch`.

## Qué hay en cada carpeta

| Carpeta | Qué es |
|---|---|
| `originales/` | Textos del juego **descifrados tal cual**, en inglés. Respaldo de seguridad (no editar) |
| `espanol/` | Textos traducidos al español (máster de la traducción) |
| `herramientas/` | Scripts: codec `KMJB` y generador del parche |
| `docs/` | Documentación técnica (formato, reversing, caracteres) |
| `parche/` | Parche generado por `build_parche.py` (no está en git, se regenera en local) |

Correspondencia de archivos: `originales/Settings/X.ini` ↔ juego `Settings/X.cdi`;
`originales/Data/LEV_Y.txt` ↔ juego `Data/LEV_Y.cdt`;
`originales/Data/LEV_Y.map` ↔ juego `Data/LEV_Y.cdm`.

## Herramientas

Codec `herramientas/kmjb.py` del formato `KMJB` (XOR por DWORDs con rotación,
ver `docs/formato-KMJB.md`):

Codec del formato `KMJB` (XOR por DWORDs con rotación, ver `docs/formato-KMJB.md`):

```
python kmjb.py decode  <origen.cdi> <destino.ini>   # descifrar un archivo
python kmjb.py encode  <origen.ini> <destino.cdi>   # cifrar un archivo
python kmjb.py batch      <carpeta_origen> <carpeta_destino>  # descifrar todos
python kmjb.py roundtrip  <carpeta>                 # verificar descifrar→cifrar = original
```

Regla de extensiones al codificar: `.ini`→`.cdi`, `.txt`→`.cdt`, `.map`→`.cdm`,
siempre con magic `KMJB`.

## Generar el parche

`herramientas/build_parche.py`:

```
python build_parche.py     # todo espanol/ -> parche/ (listo para copiar al juego)
```

Qué hace: las líneas **sin traducir** las copia byte a byte del original (conserva
ruso, comentarios polacos, etc.); las traducidas las normaliza al set del juego
(válidos `áéíóúÁÉÍÓÚüÜ`, `ñ→n`, `Ñ→N`, `¡→!`, `¿→?`, ver `docs/limitacion-caracteres.md`)
y las codifica en cp1252 (**1 byte/letra**, UTF-8 corrompe el texto en juego).
Cada archivo se verifica tras generarlo.

## Instalar el parche

Requisito: juego instalado, **versión 1.02 UK**.

1. **Respaldo:** copia las carpetas `Settings` y `Data` del juego
   (ej. `C:\Program Files (x86)\JoWooD\ColdZero\`) a un lugar seguro.
2. Genera `parche/` con `python herramientas/build_parche.py` y copia su contenido
   encima de la carpeta del juego, manteniendo la estructura
   (`parche/Settings/...` → `Settings/...`, `parche/Data/...` → `Data/...`).
   Windows pedirá permiso de administrador.
3. Juega. Para volver al inglés, restaura tu respaldo.

Notas: las voces quedan en inglés (son audio, no texto) y las letras `ñ ¡ ¿`
se muestran como `n ! ?` (las fuentes del juego no traen esos glifos).

## Mejorar la traducción

Edita el texto en `espanol/` (sin tocar claves `[xxx]` ni códigos `%d`/`%s`),
regenera con `build_parche.py` y prueba en el juego con copia de seguridad.
