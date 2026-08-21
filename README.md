# Predios Patrimoniales LADM-COL — San Andrés, Providencia y Santa Catalina

Geodatabase de los predios patrimoniales del Departamento Archipiélago de San Andrés,
Providencia y Santa Catalina, estructurada bajo el **Modelo Extendido Catastro-Registro
LADM-COL V4.1** (ICDE, Acuerdo 002 de diciembre 2023).

> **Repositorio privado.** Esta base de datos contiene información de propietarios
> (nombres, NIT), direcciones, avalúos catastrales y matrículas inmobiliarias.
> No la hagas pública ni la compartas por fuera de las personas autorizadas por
> la Gobernación.

## Contenido

| Archivo | Descripción |
|---|---|
| `LADM_COL_Predios_Patrimoniales.gdb/` | Geodatabase (formato ArcGIS File Geodatabase) con las clases del modelo LADM-COL: `LA_Predio`, `LA_Derecho`, `LA_Interesado`, `LA_FuenteAdministrativa`, `U_Terreno`, `CR_UnidadConstruccion`, `CR_ZonaHomogenea`, `AUD_Estandarizacion`. |

## Cómo abrirla en ArcGIS Pro

1. Clona o descarga este repositorio en tu equipo.
2. Abre **ArcGIS Pro** y crea (o abre) un proyecto.
3. En el panel **Catalog**, clic derecho sobre **Databases** → **Add Database**.
4. Selecciona la carpeta `LADM_COL_Predios_Patrimoniales.gdb`.
5. Despliega la conexión para ver las clases y tablas; doble clic para abrir la tabla de atributos, o arrástralas al mapa para visualizar la geometría.

## Requisitos

- ArcGIS Pro (o cualquier software compatible con File Geodatabase de Esri: QGIS con el driver OpenFileGDB, ArcGIS Desktop, etc.).
