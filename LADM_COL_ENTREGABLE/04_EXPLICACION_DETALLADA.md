# Estandarización y adaptación al modelo LADM-COL
## Predios patrimoniales — Departamento Archipiélago de San Andrés, Providencia y Santa Catalina

**Insumo:** `base de datos depurada.shp` (capa de polígonos, ArcGIS Pro)
**Modelo de referencia:** Modelo Extendido **Catastro-Registro LADM-COL V4.1**, apoyado en el **Núcleo LADM-COL V4.0.1** (ICDE, Acuerdo 002 de diciembre 2023)
**Producto:** File Geodatabase `LADM_COL_Predios_Patrimoniales.gdb`
**Sistema de referencia:** MAGNA-SIRGAS / Origen Nacional (conservado del insumo)

---

## 1. Resumen ejecutivo

Se tomó la base catastral depurada de la Gobernación (884 predios, formato IGAC con
Registro 1 jurídico y Registro 2 económico/físico) y se construyó una base de datos
**estandarizada y estructurada según el modelo LADM-COL**, conteniendo **únicamente los
70 predios patrimoniales verificados** como propiedad del Departamento.

El problema central —que el propietario aparecía escrito de muchas formas distintas,
impidiendo localizar los predios patrimoniales— quedó resuelto: las múltiples variantes
se unificaron en **un único interesado** normalizado.

| Indicador | Antes | Después |
|---|---|---|
| Registros | 884 (mezclados) | **70** (solo patrimoniales verificados) |
| Variantes del nombre del propietario (en los 70) | 4 grafías | **1 nombre canónico** |
| Variantes del NIT (en los 70) | 6 valores | **1 NIT: 892400038-2** |
| Estructura | 1 tabla plana, 80 campos | **5 clases LADM-COL + auditoría** |
| Listas controladas (dominios) | 0 | **7 dominios** |

**Cifras de los 70 predios:** 41 bienes de uso público, 29 bienes fiscales · 67 con
matrícula inmobiliaria (ORIP 450), 3 sin matrícula · área total ≈ **42,45 ha** ·
avalúo catastral total ≈ **$64.002.748.000**.

---

## 2. Diagnóstico del insumo

El shapefile tiene 80 campos que corresponden al formato del IGAC:
- **Identificación:** `CODIGO` (Número Predial Nacional de 30 dígitos), `CODIGO_ANT` (código anterior).
- **Registro 1 (jurídico):** `R1_Nombre`, `R1_TipoDoc`, `R1_NoDocum`, `R1_Direcci`, `R1_Destino`, `R1_AreaTer`, `R1_AreaCon`, `R1_Avaluo`...
- **Registro 2 (económico/físico):** matrícula, zonas, construcciones, destino económico, etc.
- **Geometría:** polígono del terreno.

### 2.1 El problema de estandarización (confirmado)
El propietario es siempre la misma entidad —el **Departamento Archipiélago de San Andrés,
Providencia y Santa Catalina, NIT 892.400.038-2**— pero estaba escrito de formas distintas.
En el total de la base aparecían ~24 combinaciones nombre+documento referidas a esa entidad
(`DEPARTAMENTO-ARCHIPIELAGO-DE-SAN-ANDRES`, `DEPARTAMENTO-ARCHIPIELAGO-SAN-AND`,
`GOBERNACION-DE-SAN-ANDRES-PROVIDE`, `MUNICIPIO-DE-SAN ANDRES`...), y el propio NIT tenía
errores de digitación (`892400038-20`, `0092400038-2`, `924000380`, `892400382`...).
Esto es exactamente lo que impedía consultar de forma confiable los predios patrimoniales.

### 2.2 Otros problemas detectados
- Codificación de caracteres dañada en `Cond` ("Público"→"P�blico") y `PH` ("Sí"→"S�").
- Campos categóricos en códigos crudos sin descripción (`R1_Destino` en una letra).
- Campos completamente vacíos (`entidad`, `defensa`, `N`).
- Áreas registrales (`R1_AreaTer`) que no siempre coinciden con el área real del polígono.

---

## 3. Selección de los 70 predios

Se cruzó el archivo Excel `Predios_Propietario_Departamento` (predios ya verificados como
propiedad de San Andrés) contra el shapefile, usando el `CODIGO` (NPN) como llave:
- Excel: 71 filas → 1 era un texto inválido ("34 objeto de avaluo") → **70 códigos válidos**.
- Los 70 cruzaron correctamente con el shapefile.

Solo estos 70 predios pasan a la base LADM-COL final. El resto de los 884 se descarta de
este producto (sigue disponible en el shapefile original).

---

## 4. Por qué el Modelo Extendido Catastro-Registro

De los cuatro esquemas del IGAC entregados:
- **Núcleo LADM-COL 4.0.1** — base conceptual (clases `LA_*`). Se usa como fundamento.
- **Modelo Extendido Catastro-Registro V4.1** — ✅ **el aplicable.** Modela predios,
  interesados, derechos (dominio), unidades espaciales y fuentes registrales. Es justamente
  el caso de predios patrimoniales con matrícula inmobiliaria.
- **Modelo NARP V1.0** y **Modelo Territorialidades Indígenas V1.0** — ❌ no aplican: son para
  titulación **colectiva** de comunidades étnicas, no para predios de una entidad pública.

---

## 5. Estructura LADM-COL construida

La base plana de 80 campos se descompone en clases relacionadas (modelo entidad-relación
propio de LADM-COL):

| Clase (GDB) | Equivalente LADM-COL | Qué representa | Registros |
|---|---|---|---|
| `U_Terreno` (feature class) | `LA_SpatialUnit` | Geometría del terreno (polígono) | 70 |
| `LA_Predio` (tabla) | `LA_BAUnit` / `CR_Predio` | El predio (unidad administrativa) | 70 |
| `LA_Interesado` (tabla) | `LA_Party` / `CR_Interesado` | El propietario | **1** |
| `LA_Derecho` (tabla) | `LA_RRR` / `CR_Derecho` | El derecho de dominio | 70 |
| `LA_FuenteAdministrativa` (tabla) | `LA_AdministrativeSource` | Soporte registral (matrícula) | 67 |
| `AUD_Estandarizacion` (tabla) | — | Trazabilidad (valores originales) | 70 |

**Relaciones (relationship classes):**
- `LA_Predio` 1—1 `U_Terreno` (cada predio tiene su terreno).
- `LA_Predio` 1—* `LA_Derecho` (sobre un predio recaen derechos).
- `LA_Interesado` 1—* `LA_Derecho` (un interesado es titular de varios derechos).
- `LA_FuenteAdministrativa` 1—* `LA_Derecho` (la matrícula soporta el derecho).

La ventaja del modelo se ve aquí: en vez de repetir el nombre del propietario 70 veces (con
sus errores), **existe un solo registro de interesado** y los 70 derechos lo referencian.

---

## 6. Transformaciones aplicadas (estandarización)

| Campo origen | Transformación |
|---|---|
| `R1_Nombre` | **Unificado** a `DEPARTAMENTO ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA` |
| `R1_NoDocum` | **Corregido** a `892400038-2` (se eliminan errores de digitación) |
| `R1_TipoDoc` = "N" | Normalizado a dominio `NIT` |
| `Cond` | "Público"→`Bien_Uso_Publico`, "Privado"→`Bien_Fiscal` (corrige acentos dañados) |
| `PH` | "Sí/No" → dominio `Si/No` (corrige "S�") |
| `R1_Destino` | Se conserva el código + se decodifica la descripción (dominio) |
| `R2_Matricu` | Se traslada a `LA_FuenteAdministrativa` (ORIP 450) |
| Geometría | El área se **recalcula del SIG** (`area_terreno_m2`, `area_terreno_ha`) |
| Valores originales | Se preservan SIN cambios en `AUD_Estandarizacion` (auditoría) |

Todos los campos llevan listas controladas (dominios) donde aplica: `dom_TipoInteresado`,
`dom_TipoDocumento`, `dom_TipoDerecho`, `dom_CondicionPredio`, `dom_DestinoEconomico`,
`dom_TipoFuente`, `dom_SiNo`.

### ⚠️ Punto a validar — destinación económica
Los códigos de `R1_Destino` vienen en una sola letra. Se decodificaron con seguridad
`A=Habitacional, B=Industrial, C=Comercial, E=Minero, F=Cultural, G=Recreacional,
H=Salubridad, I=Institucional, J=Educativo`. Los códigos `D, K, P, R, S` quedaron marcados
**"POR VALIDAR IGAC"** porque la tabla de letras varía entre resoluciones del IGAC. Conviene
notar que `D` (decodificado provisionalmente como *Agropecuario*) es el más frecuente (16),
lo cual es atípico para predios urbanos: **debe confirmarse contra la tabla del IGAC vigente
del origen de los datos** y ajustarse el diccionario `DESTINO` en el script si es necesario.

---

## 7. Cómo generar el `.gdb` (en tu ArcGIS Pro)

> Este `.gdb` solo puede crearlo ArcGIS Pro. El script lo construye en un clic.

1. Abre **ArcGIS Pro**.
2. Pestaña **Análisis → Python** (ventana de Python) o **Catálogo → carpeta → Nuevo → Notebook**.
3. Pega el contenido de `01_CONSTRUIR_GDB_LADM_COL.py`.
4. Verifica la línea `CARPETA = r"C:\Users\nicol\Downloads\BASE_DATOS"` (cámbiala si moviste la carpeta).
5. **Ejecuta.** Se crea `LADM_COL_Predios_Patrimoniales.gdb` con feature class, tablas,
   dominios y relaciones, ya cargada con los 70 predios estandarizados.

El script lee el shapefile original y aplica internamente la misma estandarización descrita,
así que el resultado es reproducible y auditable.

---

## 8. Contenido del entregable

| Archivo | Descripción |
|---|---|
| `01_CONSTRUIR_GDB_LADM_COL.py` | Script que construye el `.gdb` LADM-COL en ArcGIS Pro |
| `02_ESQUEMA_ADAPTACION_LADM_COL.png` | Diagrama del modelo y el mapeo (estilo IGAC) |
| `03_TABLA_MAPEO_CAMPOS.csv` | Trazabilidad campo origen → clase/atributo LADM-COL |
| `04_EXPLICACION_DETALLADA.md` | Este documento |
| `00_revision_antes_despues.csv` | Antes/después de cada predio (para revisión) |
| `LADM_Interesado.csv`, `LADM_Predio.csv`, `LADM_Derecho.csv`, `LADM_FuenteAdministrativa.csv`, `LADM_AUD_Estandarizacion.csv` | Tablas estandarizadas (vista previa de lo que cargará el script) |

---

## 9. Verificación y siguientes pasos sugeridos
1. Abrir `00_revision_antes_despues.csv` y validar el antes/después.
2. Confirmar la decodificación de destinación económica (`D, K, P, R, S`) con el IGAC.
3. Ejecutar el script en ArcGIS Pro y revisar la GDB resultante.
4. (Opcional) Completar matrícula en los 3 predios que no la tienen.
5. (Opcional) Cargar el detalle del Registro 2 (construcciones) si se requiere a futuro.
