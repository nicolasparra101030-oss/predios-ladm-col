# Predios Patrimoniales LADM-COL — Departamento Archipiélago de San Andrés, Providencia y Santa Catalina

Base de datos catastral de los predios patrimoniales del Departamento, estandarizada y
adaptada al **Modelo Extendido Catastro-Registro LADM-COL V4.1** (ICDE, Acuerdo 002 de
diciembre 2023), sobre el Núcleo LADM-COL V4.0.1.

> **Repositorio privado.** Contiene información de propietarios, NIT, direcciones,
> avalúos catastrales y matrículas inmobiliarias. No hacer público ni compartir por
> fuera de las personas autorizadas por la Gobernación.

## Resumen

| Indicador | Antes | Después |
|---|---|---|
| Registros | 884 (mezclados) | **70** (solo patrimoniales verificados) |
| Variantes del nombre del propietario | 4 grafías | **1 nombre canónico** |
| Variantes del NIT | 6 valores | **1 NIT: 892400038-2** |
| Estructura | 1 tabla plana, 80 campos (formato IGAC) | **5 clases LADM-COL + auditoría** |
| Listas controladas (dominios) | 0 | **7 dominios** |

Detalle completo del proceso en [`LADM_COL_ENTREGABLE/04_EXPLICACION_DETALLADA.md`](LADM_COL_ENTREGABLE/04_EXPLICACION_DETALLADA.md).

## Estructura del repositorio

```
├── LADM_COL_Predios_Patrimoniales.gdb/   # Geodatabase final (modelo LADM-COL) — ábrela en ArcGIS Pro
├── LADM_COL_ENTREGABLE/                  # Scripts, documentación y tablas del proceso de migración
│   ├── 00_DIAGNOSTICO.py
│   ├── 01_CONSTRUIR_GDB_LADM_COL.py      # Construye la gdb a partir del shapefile depurado
│   ├── 05_EXTENDER_R2_CONSTRUCCIONES_ZONAS.py
│   ├── 06_GENERAR_ESQUEMA.py
│   ├── 03_TABLA_MAPEO_CAMPOS.csv         # Mapeo campo IGAC -> campo LADM-COL
│   ├── 04_EXPLICACION_DETALLADA.md       # Explicación técnica del proceso
│   ├── 07_DOCUMENTO_ESQUEMA_BD.md/.docx  # Esquema de la base de datos (3FN, dominios, relaciones)
│   ├── GUIA_LADM_COL_EXPLICADA.md        # Guía conceptual del modelo LADM-COL aplicado
│   └── LADM_*.csv                        # Export plano de cada clase (Predio, Derecho, Interesado, etc.)
├── base de datos depurada.*              # Shapefile original (insumo, formato IGAC, 884 predios)
├── Predios_Propietario_Departamento (1).xlsx
├── MODELO NÚCLEO LADM_COL VERSIÓN 4_0_1.png
├── Modelo_Extendido_LADMCOL_Cat_Reg_V4_1.png
└── Modelo_Aplicación_LADM_COL_Predios_*.png
```

## Cómo abrir la geodatabase en ArcGIS Pro

1. Crea o abre un proyecto de ArcGIS Pro.
2. Panel **Catalog** → clic derecho en **Databases** → **Add Database**.
3. Selecciona `LADM_COL_Predios_Patrimoniales.gdb`.
4. Despliega la conexión para ver las clases: `LA_Predio`, `LA_Derecho`, `LA_Interesado`,
   `LA_FuenteAdministrativa`, `U_Terreno`, `CR_UnidadConstruccion`, `CR_ZonaHomogenea`,
   `AUD_Estandarizacion`.

## Estado de la migración

- Campo `destino_economico` (tabla `LA_Predio`): decodificado desde el código de una letra
  del IGAC (`R1_Destino`). Las categorías D, K, P, R, S fueron verificadas contra el
  dominio oficial vigente `CR_DestinacionEconomicaTipo` (Resolución 1040 de 2023 /
  LADM-COL V4.1) y ya no llevan la marca `(POR VALIDAR IGAC)`.
- Pendiente: 3 predios con código de destino `T` o `L`, que no estaban mapeados en el
  script original y quedaron sin descripción — revisar antes de publicar reportes que
  usen ese campo.

## Reproducir la migración desde cero

```bash
# Requiere ArcGIS Pro (arcpy) instalado
python LADM_COL_ENTREGABLE/01_CONSTRUIR_GDB_LADM_COL.py
python LADM_COL_ENTREGABLE/05_EXTENDER_R2_CONSTRUCCIONES_ZONAS.py
```

## Referencias

- [Modelos LADM_COL — ICDE](https://www.icde.gov.co/gestion-y-estandares/modelos-ladmcol)
- [Diccionario de Datos — Modelo Extendido Catastro Registro LADM_COL V4.1](https://www.icde.gov.co/sites/default/files/2024-09/Diccionario_de_Datos_Modelo_Extendido_Catastro_Registro_v4_1.pdf)
