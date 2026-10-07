# Formato KMJB — archivos codificados de ColdZero

> Válido para la **versión 1.02 UK**. En otras versiones, verificar magics y keys.

## Archivos afectados

- `Settings\*.cdi` (← `*.ini`), `Data\*.cdt` (← `*.txt`), `Data\*.cdm` (← `*.map`)
- 250 archivos verificados. `Data\*.LV2`, texturas y modelos usan `DE ZLock1` (otro formato, sin texto traducible).

## Algoritmo (reversado de `ColdZero.exe` con Ghidra)

| Rutina | Dirección | Papel |
|---|---|---|
| `FUN_004dcb15` (+`...cd0c`, `...cdf3`) | `004dcb15` | Lee clave con `GetPrivateProfileStringA` **y** con lector propio, compara; si difieren muestra `ERROR : Ini decoding FAILURE !` |
| `FUN_004dca3c` | `004dca3c` | Reescribe la extensión pedida: `ini→cdi`, `txt→cdt`, `map→cdm` (`c`=0x63, `d`=0x64, `t/i/m`) |
| `FUN_004dd6e7` | `004dd6e7` | Abre con `CreateFileA`, lee con `ReadFile`, detecta magic y decodifica en memoria |
| `FUN_004dd972` / `FUN_004dda01` | `004dd972`/`004dda01` | Comparan el primer DWORD con `0051741c`=`KMJB` / `00517424`=`AACL` |
| `FUN_004dd99b` / `FUN_004dda2a` | `004dd99b`/`004dda2a` | XOR por DWORDs con rotación |

## Codec

```
magic (4 bytes, sin cifrar): b'KMJB' -> key 0xA8C15E3D
                             b'AACL' -> key 0xDAC1A666
datos: DWORD[i] ^= key; key = ROL32(key, 1)   // rota 1 bit a la izquierda por DWORD
rango: del offset 4 hasta EOF (último DWORD parcial incluido, little-endian)
```

XOR es simétrico: **codificar y decodificar son la misma operación**.
Verificado: descifrar→cifrar reproduce los 250 originales byte por byte
(`kmjb.py roundtrip`: 208/208 Settings, 42/42 Data).

## Contenido descodificado

- `.ini`: formato INI clásico (`[seccion]` + `clave = valor`). Menús, textos generales, tiendas, skills.
- `.txt`: diálogos por nivel (`[SR_1]` … texto libre, una entrada por línea(s)).
- `.map`: datos de misión (mayoría numérico, algo de texto).
- Ojo: hay `printf`-style (`%d`, `%s`) y códigos que no deben traducirse ni reordenarse sin cuidado.

## Cómo generar el parche

1. Traducir copias en `espanol/` (nunca tocar `originales/`).
2. `python herramientas\kmjb.py encode espanol\Settings\X.ini salida\X.cdi`
   (para `.txt`→`.cdt`, `.map`→`.cdm`; el magic siempre `KMJB` en estos archivos).
3. Probar en el juego con copia de seguridad de los originales.
