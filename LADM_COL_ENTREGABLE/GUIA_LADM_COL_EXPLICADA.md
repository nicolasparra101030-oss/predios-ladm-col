# Guía completa: el modelo LADM-COL y su implementación en los predios patrimoniales de San Andrés

**De cero a experto.** Esta guía está escrita para alguien que nunca ha oído hablar de LADM, catastro o geodatabases. Si la lees completa y en orden, vas a entender (1) qué es el modelo, (2) por qué existe, (3) cómo se aplicó a este proyecto concreto, (4) qué se cambió respecto a los datos originales y por qué eso es mejor, y (5) cómo se construyó técnicamente, paso a paso.

- **Proyecto:** Base de datos de predios patrimoniales del Departamento Archipiélago de San Andrés, Providencia y Santa Catalina (NIT 892.400.038-2).
- **Insumo:** `base de datos depurada.shp` (884 predios en total).
- **Resultado:** `LADM_COL_Predios_Patrimoniales.gdb` (geodatabase con 70 predios verificados, organizada según LADM-COL).
- **Herramienta:** ArcGIS Pro + Python (`arcpy`).

---

## Índice

1. [Conceptos básicos (lee esto primero)](#1-conceptos-basicos)
2. [¿Qué es LADM y qué es LADM-COL?](#2-que-es-ladm)
3. [Las 4 preguntas que responde el modelo](#3-las-4-preguntas)
4. [El modelo aplicado a NUESTRO caso](#4-el-modelo-aplicado)
5. [Diccionario de las tablas creadas](#5-diccionario-de-tablas)
6. [Los dominios (listas controladas)](#6-dominios)
7. [Las relaciones entre tablas](#7-relaciones)
8. [Qué se cambió respecto a los datos originales y por qué conviene](#8-que-se-cambio)
9. [Cómo se implementó, paso a paso (el script)](#9-implementacion-paso-a-paso)
10. [Problemas técnicos que aparecieron y cómo se resolvieron](#10-problemas-tecnicos)
11. [Cómo verificar que quedó bien](#11-verificacion)
12. [Glosario](#12-glosario)

---

<a name="1-conceptos-basicos"></a>
## 1. Conceptos básicos (lee esto primero)

Antes de hablar de LADM necesitas cuatro ideas. Con esto entiendes el resto.

**a) ¿Qué es un predio?**
Un predio es una porción de tierra con un dueño y unos límites. En Colombia cada predio tiene un identificador único de 30 dígitos llamado **Número Predial Nacional (NPN)**. Ejemplo: `880010100000002600017000000000`. Ese número codifica departamento, municipio, zona, sector, manzana, predio, etc. Es como la "cédula" del predio.

**b) ¿Qué es un shapefile (.shp)?**
Es un formato de archivo para guardar **mapas con datos**. Cada fila es un predio y tiene dos cosas: una **geometría** (el polígono dibujado en el mapa: dónde está y qué forma tiene) y unos **atributos** (columnas con información: dueño, área, avalúo, etc.). El insumo de este proyecto es uno de estos archivos.

**c) ¿Qué es una geodatabase (.gdb)?**
Es la versión "profesional" de un shapefile. En lugar de una sola tabla suelta, una geodatabase es como una **mini base de datos** que puede tener varias tablas relacionadas entre sí, reglas de validación (dominios) y relaciones. ArcGIS la maneja como una carpeta con extensión `.gdb`. Aquí pasamos de **un shapefile plano** a **una geodatabase estructurada**.

**d) ¿Qué es un "modelo de datos"?**
Es un **acuerdo sobre cómo organizar la información**: qué tablas existen, qué columnas tiene cada una, qué valores se permiten y cómo se conectan. LADM-COL es uno de esos acuerdos, pero a nivel nacional. La idea es que todos en Colombia organicen los datos de tierras **igual**, para que se puedan intercambiar y entender entre entidades.

> **Resumen de la sección:** tomamos predios (identificados por NPN) que venían en un archivo plano (shapefile) y los reorganizamos en una base estructurada (geodatabase) siguiendo un estándar nacional (LADM-COL).

---

<a name="2-que-es-ladm"></a>
## 2. ¿Qué es LADM y qué es LADM-COL?

**LADM** significa *Land Administration Domain Model* (Modelo de Dominio para la Administración de Tierras). Es una **norma internacional: la ISO 19152**. Su propósito es dar un lenguaje común para describir la relación entre **personas**, **derechos** y **terrenos**. No importa el país: la estructura básica es la misma.

**LADM-COL** es la **adaptación colombiana** de esa norma (el "perfil país"). La define el ICDE (Infraestructura Colombiana de Datos Espaciales) y está oficializada en el **Acuerdo 002 de 2023**. Tiene dos piezas que usamos aquí:

- **Núcleo LADM-COL v4.0.1**: las clases fundamentales (interesado, derecho, predio, unidad espacial, fuente). Es el "esqueleto".
- **Modelo Extendido Catastro-Registro v4.1**: añade el detalle propio de catastro y registro (avalúo, destino económico, matrícula inmobiliaria, etc.). Es la "carne" sobre el esqueleto.

**¿Por qué usarlo?** Porque obliga a que los datos del Departamento sean **interoperables** con el IGAC, las Oficinas de Registro, el Catastro Multipropósito y cualquier otra entidad. Un dato hecho "a mano" cada quien lo organiza distinto; un dato en LADM-COL lo entiende todo el país.

---

<a name="3-las-4-preguntas"></a>
## 3. Las 4 preguntas que responde el modelo

Todo LADM gira alrededor de cuatro preguntas. Si las memorizas, entiendes el modelo entero:

| Pregunta | Concepto LADM | En palabras simples |
|---|---|---|
| **¿QUIÉN?** | `LA_Party` (Interesado) | La persona o entidad dueña / titular. |
| **¿QUÉ derecho tiene?** | `LA_RRR` (Derecho-Restricción-Responsabilidad) | El tipo de relación jurídica: propiedad, posesión, etc. |
| **¿SOBRE QUÉ?** | `LA_BAUnit` (Predio) + `LA_SpatialUnit` (Unidad espacial) | El predio (la unidad administrativa) y su terreno (el polígono en el mapa). |
| **¿CON QUÉ documento se prueba?** | `LA_Source` (Fuente administrativa) | La escritura, matrícula o acto que respalda el derecho. |

La frase que resume LADM es:

> **Un INTERESADO tiene un DERECHO sobre un PREDIO, soportado por una FUENTE.**

Todo lo demás son detalles colgados de esas cuatro cajas.

---

<a name="4-el-modelo-aplicado"></a>
## 4. El modelo aplicado a NUESTRO caso

En este proyecto las cuatro cajas se llenaron así:

- **¿QUIÉN?** → Siempre el mismo: el **Departamento Archipiélago de San Andrés** (Persona Jurídica, NIT 892400038-2). Por eso hay **un solo interesado** para los 70 predios.
- **¿QUÉ derecho?** → **Dominio** (propiedad). Son bienes del Departamento.
- **¿SOBRE QUÉ?** → Los **70 predios verificados** como propiedad del Departamento, cada uno con su polígono de terreno.
- **¿CON QUÉ?** → La **matrícula inmobiliaria** de cada predio (cuando existe), emitida por la ORIP 450 de San Andrés.

Estas cuatro cajas se convirtieron en tablas dentro de la geodatabase. El siguiente esquema muestra cómo quedan conectadas:

```
            ┌─────────────────────────┐
            │     LA_Interesado       │   (1 fila: el Departamento)
            │  "¿QUIÉN?"              │
            └───────────┬─────────────┘
                        │ es titular de
                        ▼
   ┌──────────┐   ┌─────────────────┐   ┌────────────────────────┐
   │ LA_Predio│◄──┤   LA_Derecho    ├──►│ LA_FuenteAdministrativa │
   │"¿SOBRE   │   │  "¿QUÉ derecho?"│   │ "¿CON QUÉ documento?"   │
   │  QUÉ?"   │   └─────────────────┘   └────────────────────────┘
   └────┬─────┘
        │ tiene terreno
        ▼
   ┌──────────┐
   │ U_Terreno│  (el polígono en el mapa)
   └──────────┘
```

Y además hay una tabla extra, **AUD_Estandarizacion**, que NO es parte del modelo LADM: es una **bitácora de auditoría** que guarda los valores originales antes de limpiarlos, para que siempre se pueda comprobar qué decía el dato de origen.

---

<a name="5-diccionario-de-tablas"></a>
## 5. Diccionario de las tablas creadas

La geodatabase contiene **1 feature class** (tabla con geometría) y **5 tablas** (sin geometría).

### 5.1 `U_Terreno` (feature class de polígonos) → la unidad espacial
Es la única tabla que tiene mapa. Guarda el polígono de cada terreno.

| Campo | Tipo | Qué guarda |
|---|---|---|
| `T_Id` | Texto(40) | Identificador del terreno (`TER_` + NPN). |
| `predio_id` | Texto(40) | NPN del predio al que pertenece (sirve para enlazar). |
| `area_terreno_m2` | Doble | Área calculada de la geometría, en metros cuadrados. |
| `area_terreno_ha` | Doble | La misma área en hectáreas (m² ÷ 10.000). |

### 5.2 `LA_Predio` → el predio (unidad administrativa básica)
El corazón de la base. Una fila por predio.

| Campo | Tipo | Qué guarda |
|---|---|---|
| `T_Id` | Texto(40) | Identificador del predio (`PRE_` + NPN). |
| `npn` | Texto(30) | Número Predial Nacional. |
| `codigo_anterior` | Texto(25) | Código catastral anterior. |
| `tipo_predio` | Texto(20) | "Privado" o "Publico" (derivado de la condición). |
| `condicion_predio` | Texto(25) | Bien Fiscal o Bien de Uso Público (controlado por dominio). |
| `destino_economico_cod` | Texto(4) | Letra del destino económico IGAC (A, B, C…). |
| `destino_economico` | Texto(60) | Descripción legible del destino (Habitacional, Comercial…). |
| `propiedad_horizontal` | Texto(4) | "Si" / "No" (controlado por dominio). |
| `area_terreno_geom_m2` | Doble | Área del terreno según la geometría. |
| `area_terreno_ha` | Doble | Esa área en hectáreas. |
| `area_registral_m2` | Doble | Área que figura en el registro. |
| `area_construida_m2` | Doble | Área construida. |
| `avaluo_catastral` | Doble | Avalúo catastral. |
| `direccion` | Texto(255) | Dirección del predio. |
| `matricula_inmobiliaria` | Texto(25) | Matrícula inmobiliaria. |

### 5.3 `LA_Interesado` → la persona/entidad titular
Una sola fila: el Departamento.

| Campo | Tipo | Qué guarda |
|---|---|---|
| `T_Id` | Texto(40) | Identificador (`INT_DPTO_88`). |
| `tipo_interesado` | Texto(30) | "Persona_Juridica" (controlado por dominio). |
| `tipo_documento` | Texto(30) | "NIT" (controlado por dominio). |
| `numero_documento` | Texto(30) | 892400038-2. |
| `nombre` | Texto(255) | Nombre oficial del Departamento. |

### 5.4 `LA_Derecho` → el vínculo jurídico (RRR)
Conecta interesado + predio + fuente. Una fila por predio.

| Campo | Tipo | Qué guarda |
|---|---|---|
| `T_Id` | Texto(40) | Identificador (`DER_` + NPN). |
| `tipo_derecho` | Texto(20) | "Dominio" (controlado por dominio). |
| `interesado_id` | Texto(40) | Apunta al interesado (`INT_DPTO_88`). |
| `predio_id` | Texto(40) | Apunta al predio (NPN). |
| `fuente_id` | Texto(40) | Apunta a la fuente (matrícula), si existe. |

### 5.5 `LA_FuenteAdministrativa` → el documento que prueba el derecho

| Campo | Tipo | Qué guarda |
|---|---|---|
| `T_Id` | Texto(40) | Identificador (`FUE_` + matrícula). |
| `tipo_fuente` | Texto(30) | "Matricula_Inmobiliaria" (controlado por dominio). |
| `numero` | Texto(25) | Número de matrícula. |
| `ente_emisor` | Texto(60) | "ORIP 450 - San Andres". |

### 5.6 `AUD_Estandarizacion` → bitácora de auditoría (no es LADM)
Guarda el valor **original** antes de limpiarlo, para trazabilidad.

| Campo | Qué guarda |
|---|---|
| `npn` | NPN del predio. |
| `nombre_original` | Nombre del dueño tal como venía en el shapefile. |
| `nit_original` | NIT tal como venía. |
| `cond_original` | Condición tal como venía. |
| `destino_original` | Destino económico tal como venía. |
| `ph_original` | Propiedad horizontal tal como venía. |

---

<a name="6-dominios"></a>
## 6. Los dominios (listas controladas)

Un **dominio** es una **lista cerrada de valores permitidos** para un campo. Es la diferencia entre escribir libremente (y que cada quien escriba "SI", "Sí", "si", "S") y elegir de una lista fija. Esto **garantiza que los datos sean uniformes**.

Se crearon estos dominios:

| Dominio | Para qué campo | Valores permitidos |
|---|---|---|
| `dom_TipoInteresado` | tipo de interesado | Persona Natural, Persona Jurídica, Grupo de Interesados |
| `dom_TipoDocumento` | tipo de documento | Cédula, NIT, Cédula Extranjería, Pasaporte, Sin Identificación |
| `dom_TipoDerecho` | tipo de derecho | Dominio, Posesión, Ocupación, Tenencia |
| `dom_CondicionPredio` | condición del predio | Bien de Uso Público, Bien Fiscal, Sin dato |
| `dom_TipoFuente` | tipo de fuente | Matrícula, Escritura Pública, Acto Administrativo, Sin dato |
| `dom_SiNo` | propiedad horizontal | Si, No |
| `dom_DestinoEconomico` | destino económico | Las letras IGAC (A=Habitacional, C=Comercial, …) |

**Beneficio:** ArcGIS muestra estos campos como un **menú desplegable**. Es imposible (o muy difícil) escribir un valor inválido, y se acaban las variantes tipo "Publico / público / PUBLICO".

---

<a name="7-relaciones"></a>
## 7. Las relaciones entre tablas

Una **relación** (relationship class) le dice a ArcGIS cómo están conectadas dos tablas, igual que cuando en una base de datos relacionas por una "llave". Así, al seleccionar un predio en el mapa, ArcGIS puede mostrarte automáticamente su dueño, su derecho y su matrícula.

| Relación creada | Conecta | Cardinalidad | Significado |
|---|---|---|---|
| `rc_Predio_Terreno` | Predio → Terreno | 1 a 1 | Cada predio tiene un terreno. |
| `rc_Predio_Derecho` | Predio → Derecho | 1 a muchos | Un predio puede tener varios derechos. |
| `rc_Interesado_Derecho` | Interesado → Derecho | 1 a muchos | Un interesado puede ser titular de muchos derechos. |
| `rc_Fuente_Derecho` | Fuente → Derecho | 1 a muchos | Una fuente puede soportar varios derechos. |

"1 a muchos" significa, por ejemplo, que **el Departamento (1 interesado)** está conectado con **los 70 derechos**.

---

<a name="8-que-se-cambio"></a>
## 8. Qué se cambió respecto a los datos originales y por qué conviene

Esta es la parte clave de "qué se transformó y en qué beneficia". El shapefile original tenía **884 predios y 82 columnas**, con datos sucios y mezclados. Estos fueron los cambios concretos:

### Cambio 1 — Se filtró a 70 predios verificados
- **Antes:** 884 predios de todo tipo.
- **Después:** solo los **70 predios verificados** como propiedad del Departamento (lista `VERIFICADOS` en el script).
- **Beneficio:** la base contiene únicamente lo que es jurídicamente cierto. No se mezcla lo confirmado con lo dudoso.

### Cambio 2 — Un solo interesado en vez de ~24 variantes
- **Antes:** el nombre del Departamento aparecía escrito de ~24 maneras distintas ("DEPTO ARCHIPIELAGO", "Departamento de San Andres", etc.).
- **Después:** **un único interesado canónico**: `DEPARTAMENTO ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA`, NIT `892400038-2`.
- **Beneficio:** se elimina la duplicación. Si mañana cambia un dato del Departamento, se corrige en **un solo lugar**. Las consultas "¿qué tiene el Departamento?" devuelven todo, no fragmentos.

### Cambio 3 — Limpieza de acentos y caracteres dañados
- **Antes:** texto con tildes mal codificadas (el típico `Público` que se vuelve `P�blico`).
- **Después:** texto normalizado, sin acentos rotos (función `_sin_acentos`).
- **Beneficio:** se evitan errores al comparar, buscar o exportar. Un sistema externo no se atraganta con caracteres raros.

### Cambio 4 — Valores libres convertidos en listas controladas (dominios)
- **Antes:** "Pública/privada", "SI/No/s/n" escritos a mano de mil formas.
- **Después:** valores normalizados (`limpiar_cond`, `limpiar_ph`) y forzados por dominios.
- **Beneficio:** consistencia total. Los reportes agrupan bien (no salen 8 categorías cuando hay 2).

### Cambio 5 — Áreas recalculadas desde la geometría
- **Antes:** las áreas venían como dato textual, a veces dudoso.
- **Después:** `area_terreno_m2` se **calcula del polígono real** (`SHAPE@AREA`) y se deriva la versión en hectáreas.
- **Beneficio:** el área refleja la geometría verdadera, no un número heredado posiblemente erróneo. Se conserva además el área registral aparte para poder compararlas.

### Cambio 6 — Una tabla plana se convirtió en un modelo relacional LADM
- **Antes:** 82 columnas en una sola tabla (todo mezclado: persona, predio, derecho, documento).
- **Después:** 6 tablas especializadas + relaciones, siguiendo las 4 cajas de LADM.
- **Beneficio:** interoperabilidad con IGAC/Registro/Catastro Multipropósito, sin redundancia, y consultas mucho más potentes.

### Cambio 7 — Se añadió trazabilidad (auditoría)
- **Antes:** al limpiar un dato se perdía el valor original.
- **Después:** la tabla `AUD_Estandarizacion` guarda lo que decía el dato antes de limpiarlo.
- **Beneficio:** cualquiera puede auditar la transformación y volver al origen si hace falta. Transparencia total.

> **En una frase:** se pasó de *una tabla plana, sucia y con 884 registros mezclados* a *una geodatabase estandarizada, limpia, trazable y con los 70 predios ciertos*, lista para intercambiarse con cualquier entidad del país.

---

<a name="9-implementacion-paso-a-paso"></a>
## 9. Cómo se implementó, paso a paso (el script)

El script `01_CONSTRUIR_GDB_LADM_COL.py` construye todo de forma automática. Aquí está lo que hace, en el mismo orden, explicado para que lo entiendas aunque no programes.

**Paso 0 — Parámetros.** Se define la carpeta de trabajo, el nombre del shapefile de entrada y el nombre de la geodatabase de salida. `SOBRESCRIBIR = True` significa "si ya existe la GDB, bórrala y reconstrúyela limpia".

**Paso 1 — Crear la geodatabase.** Si ya existe, la borra; luego crea una `.gdb` vacía con `CreateFileGDB`. También lee el **sistema de referencia** del shapefile (MAGNA-SIRGAS, el sistema de coordenadas oficial de Colombia) para que el mapa quede bien georreferenciado.

**Paso 2 — Crear los dominios.** Se crean las listas controladas de la sección 6 con `CreateDomain` + `AddCodedValueToDomain`. Esto se hace **antes** que las tablas, porque luego los campos se "enganchan" a estos dominios.

**Paso 3 — Crear la feature class `U_Terreno`.** Es la tabla con geometría de polígonos. Se le agregan sus campos (`T_Id`, `predio_id`, áreas).

**Paso 4 — Crear las 5 tablas.** `LA_Interesado`, `LA_Predio`, `LA_Derecho`, `LA_FuenteAdministrativa` y `AUD_Estandarizacion`, cada una con sus campos. Una función `tabla()` lo hace de forma compacta.

**Paso 5 — Asignar dominios a los campos.** Con `AssignDomainToField` se conecta, por ejemplo, el campo `condicion_predio` con el dominio `dom_CondicionPredio`. A partir de aquí, ese campo solo acepta valores de la lista.

**Paso 6 — Cargar los datos (el paso central).** Se hace en tres subpasos:
- **6.1** Se inserta el **único interesado** (el Departamento).
- **6.2** Se **lee el shapefile** fila por fila con un `SearchCursor`. Para cada predio: si su NPN **no** está en la lista de 70 verificados, se salta; si está, se limpia y estandariza (condición, destino, PH, áreas) y la fila resultante se **guarda en listas en memoria** (`filas_pre`, `filas_ter`, etc.).
- **6.3** Se **escriben las tablas una por una** con `InsertCursor`, volcando las listas. (En la sección 10 explico por qué se hace en este orden y no todo a la vez.)

**Paso 7 — Crear las relaciones.** Con `CreateRelationshipClass` se construyen las 4 relaciones de la sección 7, dejando el modelo navegable.

**Final.** El script imprime un resumen: `Predios cargados: 70 | Fuentes (matriculas): N` y la lista de tablas creadas.

---

<a name="10-problemas-tecnicos"></a>
## 10. Problemas técnicos que aparecieron y cómo se resolvieron

Durante la puesta en marcha aparecieron dos errores reales. Quedan documentados porque enseñan **buenas prácticas de `arcpy`** y porque explican por qué el código quedó como quedó.

### Problema 1 — Las tablas se creaban pero salían vacías
- **Síntoma:** la geodatabase y las tablas existían, pero en ArcGIS no se veían filas.
- **Causa:** el código cerraba los cursores de escritura con `for c in (...): del c`. Eso solo borraba la variable temporal `c`, **no los cursores reales**. Como en ArcGIS Pro las variables siguen vivas en la sesión, los cursores nunca se liberaban: quedaban **bloqueos** sobre las tablas y los datos no se confirmaban/visualizaban.
- **Solución:** liberar los cursores de verdad. Finalmente se rediseñó para usar bloques `with`, que cierran y confirman automáticamente.

### Problema 2 — `RuntimeError: workspace already in transaction mode`
- **Síntoma:** al insertar en la segunda tabla, el script reventaba con ese error.
- **Causa:** se abrían **5 `InsertCursor` al mismo tiempo** sobre la misma File GDB. Una File GDB **solo admite una transacción de edición activa**; el segundo cursor entra en conflicto.
- **Solución (la que quedó):** primero se **lee** todo el shapefile y se guardan las filas en listas; luego se **escribe cada tabla por separado**, con un único cursor abierto a la vez dentro de un bloque `with`. Así nunca hay dos transacciones simultáneas, y cada cursor se libera solo aunque algo falle.

> **Lección general:** en `arcpy` sobre File GDB, no abras varios cursores de escritura a la vez y usa siempre `with` para que se cierren y confirmen solos.

---

<a name="11-verificacion"></a>
## 11. Cómo verificar que quedó bien

1. En el **Catálogo** de ArcGIS Pro, clic derecho en la GDB → **Refresh**.
2. Abre `LA_Predio`: deben verse las filas (hasta 70).
3. Abre `U_Terreno` y agrégala al mapa: deben verse los polígonos.
4. Revisa que `LA_Interesado` tenga **una** fila (el Departamento).
5. Selecciona un predio y, gracias a las relaciones, navega a su derecho y su fuente.
6. Si necesitas comprobar la transformación de un dato, mira `AUD_Estandarizacion` para ver el valor original.

El script de diagnóstico `00_DIAGNOSTICO.py` también sirve para confirmar que el shapefile se lee bien y que los códigos coinciden, antes de reconstruir.

---

<a name="12-glosario"></a>
## 12. Glosario

- **LADM (ISO 19152):** norma internacional para administrar tierras (personas–derechos–terrenos).
- **LADM-COL:** versión colombiana de LADM (ICDE, Acuerdo 002/2023).
- **NPN (Número Predial Nacional):** identificador único de 30 dígitos de un predio.
- **Shapefile (.shp):** archivo de mapa con geometría + atributos en una sola tabla.
- **Geodatabase (.gdb):** base de datos espacial con varias tablas, dominios y relaciones.
- **Feature class:** tabla que SÍ tiene geometría (mapa).
- **Atributo:** una columna de datos (no espacial).
- **Dominio:** lista cerrada de valores válidos para un campo.
- **Relationship class:** definición de cómo se conectan dos tablas.
- **Interesado (`LA_Party`):** quién (persona o entidad).
- **Derecho / RRR (`LA_RRR`):** qué relación jurídica (propiedad, posesión…).
- **Predio / BAUnit (`LA_BAUnit`):** la unidad administrativa básica.
- **Unidad espacial (`LA_SpatialUnit`):** el terreno/polígono.
- **Fuente administrativa (`LA_Source`):** el documento que soporta el derecho.
- **Bien Fiscal:** bien del Estado de uso patrimonial/privado (puede venderse).
- **Bien de Uso Público:** bien destinado al uso de todos (parques, vías…).
- **Matrícula inmobiliaria:** folio de registro del predio en la ORIP.
- **ORIP:** Oficina de Registro de Instrumentos Públicos.
- **MAGNA-SIRGAS:** sistema de coordenadas oficial de Colombia.
- **Destino económico:** uso del predio según IGAC (habitacional, comercial…), codificado por letras.
- **arcpy:** librería de Python de ArcGIS para automatizar tareas.
- **Cursor (Insert/Search):** mecanismo de arcpy para escribir/leer filas.
- **Transacción:** bloque de cambios que se confirma de una sola vez en la base.

---

*Documento generado para el proyecto de predios patrimoniales del Departamento Archipiélago de San Andrés, Providencia y Santa Catalina. Acompaña a los scripts `00_DIAGNOSTICO.py` y `01_CONSTRUIR_GDB_LADM_COL.py`.*
