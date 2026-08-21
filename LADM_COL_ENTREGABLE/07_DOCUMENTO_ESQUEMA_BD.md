# Documento del esquema de adaptación al modelo LADM-COL
## Análisis desde la teoría de bases de datos

**Insumo original:** `base de datos depurada.shp` (tabla plana en formato IGAC)
**Producto:** File Geodatabase `LADM_COL_Predios_Patrimoniales.gdb`
**Modelo de referencia:** Modelo Extendido Catastro-Registro LADM-COL V4.1, sobre el Núcleo LADM-COL V4.0.1 (ISO 19152 — *Land Administration Domain Model*)
**Esquema visual asociado:** `02_ESQUEMA_ADAPTACION_LADM_COL.png`

> Este documento explica **teóricamente** cómo se adaptó la base de datos: el paso de un archivo plano a un modelo relacional normalizado. No describe el código ni las herramientas; se concentra en los conceptos de diseño de bases de datos.

---

## 1. Punto de partida: una tabla plana (no normalizada)

El insumo era una **única relación (tabla)** de aproximadamente 80 columnas y 884 filas, donde cada fila mezclaba, en un mismo registro, información que en realidad pertenece a entidades distintas del mundo real:

- la **identidad del predio** (número predial, código anterior, dirección),
- el **propietario** (nombre, documento, tipo de documento),
- el **derecho** que vincula propietario y predio,
- el **soporte registral** (matrícula inmobiliaria),
- las **características físicas/económicas** de las construcciones y del terreno (Registro 2),
- la **geometría** del polígono.

Este diseño «todo en una tabla» se denomina **estructura desnormalizada** y presenta los problemas clásicos que la teoría relacional busca evitar:

| Problema (teoría) | Manifestación en el insumo |
|---|---|
| **Redundancia de datos** | El propietario (siempre la misma entidad) se repetía en cientos de filas. |
| **Anomalías de actualización** | Corregir el NIT obligaría a editar muchas filas; bastaba olvidar una para crear inconsistencia. |
| **Anomalías de inserción** | No se podía registrar una matrícula o una fuente sin un predio asociado. |
| **Anomalías de borrado** | Borrar un predio eliminaba también el único rastro de su propietario o su matrícula. |
| **Falta de integridad de dominio** | Campos categóricos en texto libre o códigos crudos, con erratas y acentos dañados. |
| **Dependencias parciales/transitivas** | Atributos del propietario y de la construcción dependían de claves que no eran la clave del predio. |

La presencia de **~24 variantes de nombre + documento** para un mismo propietario (el Departamento, NIT 892.400.038-2) es el síntoma textbook de la redundancia: el mismo hecho del mundo real almacenado muchas veces y, por tanto, capaz de divergir.

---

## 2. Objetivo del diseño: normalización

La adaptación consistió en **descomponer** esa única relación en varias relaciones más pequeñas, cada una describiendo **una sola clase de entidad**, conectadas mediante claves. Este proceso es la **normalización**, y el resultado satisface las formas normales:

- **1FN (Primera Forma Normal):** cada atributo es atómico. Donde el insumo guardaba hasta 3 construcciones y 2 zonas en columnas repetidas en la misma fila (`R2_Habitac`, `R2_Habit_1`, `R2_Habit_2`…), el modelo lo convierte en **filas** de tablas hijas (`CR_UnidadConstruccion`, `CR_ZonaHomogenea`). Se elimina el «grupo repetitivo».
- **2FN (Segunda Forma Normal):** ningún atributo no clave depende sólo de una parte de la clave. Los datos del propietario, que no dependen del predio sino del interesado, se trasladan a `LA_Interesado`.
- **3FN (Tercera Forma Normal):** se eliminan dependencias transitivas. La descripción de un código (p. ej. destino económico) no se almacena junto al predio sino que se resuelve mediante **dominios** (listas controladas).

El modelo conceptual de referencia (LADM-COL / ISO 19152) ya es, por construcción, un **modelo entidad-relación normalizado**. Adaptar el insumo a LADM-COL equivale, en términos de bases de datos, a **proyectar una tabla plana sobre un esquema relacional normalizado preexistente**.

---

## 3. Los tres niveles del diseño

La teoría distingue tres niveles de abstracción; el proyecto los recorre así:

| Nivel | En este proyecto |
|---|---|
| **Conceptual** | El modelo LADM-COL: entidades *Interesado, Predio, Derecho, Fuente, Unidad espacial* y sus relaciones. Independiente de cualquier software. Es el modelo entidad-relación «universal» del dominio catastral. |
| **Lógico** | La traducción a tablas relacionales con claves primarias y foráneas, atributos tipados y dominios. Es lo que describe el esquema PNG. |
| **Físico** | La materialización como File Geodatabase: *feature class*, tablas, *coded value domains* y *relationship classes*, con tipos de dato concretos (TEXT, DOUBLE, SHORT, LONG) y un sistema de referencia espacial (MAGNA-SIRGAS / Origen Nacional). |

---

## 4. Las entidades del modelo (relaciones resultantes)

Cada tabla representa **una entidad** con su **clave primaria** `T_Id` (identificador único LADM-COL). A continuación, su rol en términos de base de datos.

### 4.1 `LA_Interesado` — la entidad «propietario»
- **Clave primaria:** `T_Id`.
- **Razón de existir:** factoriza la información del titular para que **exista una sola vez**. Aquí se materializa el mayor beneficio de la normalización: las ~24 variantes colapsan en **un único registro canónico**. Cualquier corrección futura del nombre o el NIT se hace en un solo lugar (se elimina la anomalía de actualización).
- **Atributos con dominio:** `tipo_interesado`, `tipo_documento` (integridad de dominio).

### 4.2 `LA_Predio` — la entidad central «predio»
- **Clave primaria:** `T_Id`; **clave natural/candidata:** `npn` (número predial nacional de 30 dígitos, único por predio).
- **Rol:** es la entidad alrededor de la cual gira el modelo (en LADM-COL, la *Basic Administrative Unit*). Contiene sólo atributos que dependen funcionalmente del predio: condición, destino, áreas, avalúo, dirección.
- **Distinción importante de calidad de dato:** se conservan en paralelo el **área registral** (declarada en el documento) y el **área geométrica** (calculada del polígono). Mantener ambas es una decisión de diseño: representan dos hechos distintos y permiten auditar discrepancias.

### 4.3 `LA_Derecho` — la entidad asociativa (relación N:M resuelta)
- **Clave primaria:** `T_Id`.
- **Claves foráneas:** `interesado_id` → `LA_Interesado`, `predio_id` → `LA_Predio`, `fuente_id` → `LA_FuenteAdministrativa`.
- **Concepto clave:** un derecho es la **entidad asociativa** (tabla puente) que materializa la relación entre *quién* (interesado), *sobre qué* (predio) y *con qué soporte* (fuente). Conceptualmente, la relación «interesado posee predios» es de muchos-a-muchos; en el modelo relacional se resuelve **siempre** con una tabla intermedia, que aquí además es una entidad propia del dominio (el derecho real de dominio).

### 4.4 `LA_FuenteAdministrativa` — la entidad «soporte documental»
- **Clave primaria:** `T_Id`.
- **Rol:** almacena la matrícula inmobiliaria (ORIP 450) como entidad independiente. Esto evita repetir el dato de la matrícula y permite que **una fuente respalde uno o varios derechos** sin duplicación.

### 4.5 `U_Terreno` — la entidad espacial (*feature class*)
- **Clave primaria:** `T_Id`; **clave foránea:** `predio_id` → `LA_Predio`.
- **Rol:** separa la **geometría** (el polígono) de los **atributos alfanuméricos** del predio. Es la *Spatial Unit* del modelo. La relación con el predio es **1:1** (cada predio tiene un terreno y viceversa, en este alcance). Separar geometría de atributos es buena práctica del modelado geoespacial: una entidad gráfica, una entidad descriptiva.

### 4.6 `CR_UnidadConstruccion` — entidad hija (Registro 2 físico)
- **Clave primaria:** `T_Id`; **clave foránea:** `predio_id` → `LA_Predio`.
- **Rol:** resuelve el **grupo repetitivo** de hasta 3 construcciones por predio. En lugar de columnas repetidas (violación de 1FN), cada construcción es **una fila**. Relación con el predio: **1:N**.
- **Atributo con dominio:** `estrato` (1..6).

### 4.7 `CR_ZonaHomogenea` — entidad hija (Registro 2 económico del terreno)
- **Clave primaria:** `T_Id`; **clave foránea:** `predio_id` → `LA_Predio`.
- **Rol:** igual lógica que la anterior, para hasta 2 segmentos de zona homogénea (física y geoeconómica). Relación **1:N**.

### 4.8 `AUD_Estandarizacion` — la tabla de trazabilidad (auditoría)
- **Enlace:** `npn`, que referencia el predio.
- **Rol:** conserva los **valores originales** (nombre, NIT, condición, destino, PH tal como venían) antes de la estandarización. En términos de bases de datos es una **tabla de auditoría / historización**: documenta la procedencia del dato (*data lineage*) y permite revertir o verificar cualquier transformación. Garantiza que normalizar no destruya información: lo que se «limpió» queda registrado.

---

## 5. Claves e integridad referencial

El modelo se sostiene sobre tres tipos de claves:

- **Clave primaria (PK):** `T_Id` en cada tabla. Identificador artificial (*surrogate key*) único, estable, independiente de los datos descriptivos.
- **Clave natural / candidata:** `npn` en `LA_Predio` (identifica el predio en el mundo real).
- **Clave foránea (FK):** todo atributo `*_id` apunta al `T_Id` del registro padre. Esta convención uniforme («la FK del hijo guarda el T_Id del padre») hace explícita la **integridad referencial**: no puede existir un derecho sin predio e interesado válidos, ni una construcción huérfana.

La **integridad referencial** asegura que las relaciones declaradas nunca apunten a registros inexistentes; las **relationship classes** del modelo físico hacen cumplir y navegar estos vínculos.

---

## 6. Integridad de dominio (listas controladas)

Donde el insumo tenía texto libre o códigos crudos, el modelo define **dominios** (en teoría relacional, restricciones `CHECK` / catálogos de valores; en la GDB, *coded value domains*). Cada dominio es un par **código → descripción** que restringe los valores admisibles de un campo:

| Dominio | Campo(s) que controla |
|---|---|
| `dom_TipoInteresado` | naturaleza del interesado |
| `dom_TipoDocumento` | tipo de documento de identidad |
| `dom_TipoDerecho` | tipo de derecho (dominio, posesión…) |
| `dom_CondicionPredio` | bien de uso público / bien fiscal |
| `dom_TipoFuente` | tipo de fuente administrativa |
| `dom_DestinoEconomico` | destinación económica (código IGAC) |
| `dom_SiNo` | propiedad horizontal |
| `dom_Estrato` | estrato socioeconómico (1..6) |

Beneficio teórico: se garantiza la **consistencia de los valores categóricos** (no más «Público»/«P�blico»/«PUBLICO» como tres valores distintos) y se habilita decodificación legible sin almacenar la descripción en cada fila (evita dependencia transitiva → 3FN).

---

## 7. Cardinalidades del modelo (modelo entidad-relación)

Las relaciones y sus cardinalidades, tal como las muestra el esquema PNG:

| Relación | Cardinalidad | Lectura |
|---|---|---|
| `LA_Interesado` — `LA_Derecho` | 1 : N | un interesado es titular de varios derechos |
| `LA_Predio` — `LA_Derecho` | 1 : N | sobre un predio pueden recaer varios derechos |
| `LA_FuenteAdministrativa` — `LA_Derecho` | 1 : N | una fuente soporta varios derechos |
| `LA_Predio` — `U_Terreno` | 1 : 1 | cada predio tiene un terreno |
| `LA_Predio` — `CR_UnidadConstruccion` | 1 : N | un predio tiene varias construcciones |
| `LA_Predio` — `CR_ZonaHomogenea` | 1 : N | un predio tiene varios segmentos de zona |
| `LA_Predio` — `AUD_Estandarizacion` | 1 : 1 | un predio tiene su registro de auditoría |

La relación lógica **interesado ↔ predio** es de muchos-a-muchos (N:M) y queda **resuelta** a través de la entidad asociativa `LA_Derecho`, que la descompone en dos relaciones 1:N. Esta es la técnica estándar para implementar N:M en el modelo relacional.

---

## 8. Calidad de datos y reducción de redundancia (antes / después)

| Dimensión | Antes (tabla plana) | Después (modelo normalizado) |
|---|---|---|
| Estructura | 1 tabla, ~80 columnas | 8 entidades relacionadas + auditoría |
| Filas | 884 mezcladas | 70 predios (alcance verificado) |
| Propietario | ~24 variantes | **1 registro canónico** |
| NIT | 6 grafías con erratas | **1 valor: 892400038-2** |
| Valores categóricos | texto libre / códigos crudos | **8 dominios** controlados |
| Grupos repetitivos | columnas `_1`, `_2` en la misma fila | **filas** en tablas hijas (1FN) |
| Trazabilidad | inexistente | **tabla de auditoría** |

---

## 9. Síntesis conceptual

La adaptación es, en esencia, una **descomposición sin pérdida** (*lossless decomposition*) de una relación universal en un esquema normalizado:

1. Se identificaron las **entidades reales** ocultas en la tabla plana.
2. Cada entidad recibió su propia relación con **clave primaria** estable (`T_Id`).
3. Las relaciones entre entidades se expresaron con **claves foráneas** e **integridad referencial**, resolviendo la relación N:M mediante la **entidad asociativa** `LA_Derecho`.
4. Los **grupos repetitivos** (construcciones, zonas) se llevaron a **tablas hijas** (1FN).
5. Los **valores categóricos** se restringieron con **dominios** (integridad de dominio, 3FN).
6. Se preservó la **procedencia** del dato en una **tabla de auditoría**, garantizando una transformación reversible y verificable.

El resultado es una base de datos que elimina la redundancia, previene las anomalías de inserción/actualización/borrado y se alinea con un estándar internacional (ISO 19152 / LADM-COL), manteniendo además la dimensión espacial integrada con la alfanumérica.
