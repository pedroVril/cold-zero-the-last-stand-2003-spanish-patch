# Limitación: caracteres españoles

## Problema

El parche funciona, pero el juego **no trae glifos para `ñ Ñ ¡ ¿`** en sus fuentes
latinas (bitmaps `.tga` en `Textures\Fonts`, a su vez cifradas con `DE ZLock1`).
Verificado con sonda en el tutorial: vocales con acento (minúsculas y mayúsculas)
y `ü` **sí** se ven; `ñ/Ñ/¡/¿` salen como basura.

## Set final soportado

Válidos (1 byte cp1252, se escriben tal cual): `á é í ó ú Á É Í Ó Ú ü Ü` +
ASCII normal. Conversión obligatoria: `ñ→n`, `Ñ→N`, `¡→!`, `¿→?`.

**Trampa importante (bug ya corregido):** los másters en `espanol/` son UTF-8,
donde `ó` ocupa 2 bytes, pero el juego lee byte a byte (`ratón` → `ratAn`).
Por eso `build_parche.py` codifica la salida en **cp1252 (1 byte/letra)** y falla
en voz alta si algo no cabe, en vez de generar basura silenciosa.

## Regla de escritura

- En `espanol/` se escribe **español correcto con acentos** (es el máster legible).
- Al generar el parche jugable, `herramientas/build_parche.py` normaliza el texto
  al set seguro del juego (ver tabla). Nunca se codifica con acentos.

## Tabla de conversión (build)

Se conservan: `A-Z a-z 0-9`, puntuación básica `.,;:!?()'"%-$+/*=`, `%d %s`,
claves `[xxx]`, prefijo `>`, teclas (`ESC CTRL SHIFT`).

## No traducible (audio y mapas de bits)

- Voces: `Settings\ft_sounds\*.ini` solo mapea `sección → .wav`; los audios quedan en inglés.
- Textos dentro de imágenes (briefings, créditos `.tga`): son gráficos, no texto.
- `Assets.bin` (descripciones de armas, texto plano): formato binario con offsets;
  se deja para fase 2 de un proceso de reversing mas profundo (requiere edición binaria cuidadosa, no es `.ini`).

## Curiosidad: `lan = ENG`

`Settings\Lgamebar.ini` tiene `lan = ENG`. Es la marca de idioma del motor, pero no
existe variante española de fuentes ni textos; **no tocar**.
