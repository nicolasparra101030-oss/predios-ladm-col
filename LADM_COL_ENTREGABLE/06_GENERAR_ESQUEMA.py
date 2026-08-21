# -*- coding: utf-8 -*-
# =============================================================================
#  GENERADOR DEL ESQUEMA (diagrama entidad-relacion) DEL MODELO LADM-COL
#  Produce:  02_ESQUEMA_ADAPTACION_LADM_COL.png
#
#  No requiere ArcGIS: solo matplotlib.  Refleja el modelo COMPLETO ya
#  consistente (FK -> T_Id del padre) incluyendo la extension del Registro 2
#  (CR_UnidadConstruccion y CR_ZonaHomogenea).
# =============================================================================
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

CARPETA = r"C:\Users\nicol\Downloads\BASE_DATOS"
OUT = os.path.join(CARPETA, "LADM_COL_ENTREGABLE", "02_ESQUEMA_ADAPTACION_LADM_COL.png")

# Colores por clase
C_INT = "#16a085"; C_DER = "#e67e22"; C_FUE = "#c0392b"; C_PRE = "#2874a6"
C_TER = "#27ae60"; C_AUD = "#7f8c8d"; C_UC = "#6c3483"; C_ZH = "#117864"
C_SRC = "#95a5a6"

fig, ax = plt.subplots(figsize=(16, 10), dpi=130)
ax.set_xlim(0, 16); ax.set_ylim(0, 10); ax.axis("off")

geom = {}  # name -> dict de geometria para anclar flechas

def clase(name, x, ytop, w, color, lines, title_size=11, line_size=7.6):
    header_h = 0.42
    body_h = max(0.55, 0.295 * len(lines) + 0.28)
    bottom = ytop - header_h - body_h
    # cuerpo
    ax.add_patch(Rectangle((x, bottom), w, body_h, facecolor="white",
                           edgecolor=color, linewidth=1.6, zorder=3))
    # encabezado
    ax.add_patch(Rectangle((x, ytop - header_h), w, header_h, facecolor=color,
                           edgecolor=color, linewidth=1.6, zorder=3))
    ax.text(x + w / 2, ytop - header_h / 2, name, ha="center", va="center",
            color="white", fontsize=title_size, fontweight="bold", zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + 0.12, ytop - header_h - 0.26 - 0.295 * i, ln, ha="left",
                va="center", fontsize=line_size, zorder=4, color="#2c3e50")
    geom[name] = dict(x=x, top=ytop, w=w, bottom=bottom,
                      cy=(ytop - header_h + bottom) / 2)

def edge(name, side):
    g = geom[name]
    if side == "left":   return (g["x"], g["cy"])
    if side == "right":  return (g["x"] + g["w"], g["cy"])
    if side == "top":    return (g["x"] + g["w"] / 2, g["top"])
    if side == "bottom": return (g["x"] + g["w"] / 2, g["bottom"])

def conecta(a, sa, b, sb, etiqueta="", rel="", color="#34495e", style="-"):
    p1 = edge(a, sa); p2 = edge(b, sb)
    arr = FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=14,
                          lw=1.4, color=color, linestyle=style,
                          shrinkA=2, shrinkB=2, zorder=2)
    ax.add_patch(arr)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    if rel:
        ax.text(mx, my + 0.14, rel, ha="center", va="bottom", fontsize=7.5,
                color="#1b4f72", fontweight="bold", zorder=5)
    if etiqueta:
        ax.text(mx, my - 0.16, etiqueta, ha="center", va="top", fontsize=6.6,
                color="#566573", zorder=5)

# --------------------------------------------------------------- TITULOS
ax.text(8, 9.78, "ESQUEMA DE ADAPTACION AL MODELO LADM-COL",
        ha="center", fontsize=17, fontweight="bold", color="#1b2631")
ax.text(8, 9.45, "Predios patrimoniales - Departamento Archipielago de San Andres, "
        "Providencia y Santa Catalina  (NIT 892.400.038-2)",
        ha="center", fontsize=9.5, color="#566573")
ax.text(8, 9.20, "Modelo Extendido Catastro-Registro LADM-COL V4.1  ·  "
        "Nucleo LADM-COL V4.0.1   |   incluye Registro 2 (construcciones y zonas homogeneas)",
        ha="center", fontsize=8.5, style="italic", color="#7f8c8d")

# --------------------------------------------------------------- CLASES
clase("base de datos\ndepurada.shp", 0.25, 8.55, 2.75, C_SRC, [
    "80 campos (1 tabla plana, IGAC)", "884 predios", "Registro 1 (juridico)",
    "Registro 2 (economico / fisico)", "+ geometria de poligono"],
    title_size=9, line_size=7.2)

clase("LA_Interesado", 3.55, 8.95, 3.0, C_INT, [
    "T_Id  (PK)", "tipo_interesado  (dom)", "tipo_documento  (dom)",
    "numero_documento", "nombre   (1 unico interesado)"])

clase("LA_Derecho", 7.55, 8.95, 2.85, C_DER, [
    "T_Id  (PK)", "tipo_derecho  (dom)", "interesado_id  (FK)",
    "predio_id  (FK)", "fuente_id  (FK)"])

clase("LA_Predio", 7.55, 6.95, 3.15, C_PRE, [
    "T_Id  (PK)", "npn  (numero predial)", "codigo_anterior",
    "condicion_predio  (dom)", "destino_economico  (dom)",
    "propiedad_horizontal  (dom)", "area_terreno_geom_m2",
    "area_registral / construida_m2", "avaluo_catastral", "direccion"])

clase("LA_FuenteAdministrativa", 3.55, 5.95, 3.0, C_FUE, [
    "T_Id  (PK)", "tipo_fuente  (dom)", "numero  (matricula)",
    "ente_emisor  (ORIP 450)"])

clase("AUD_Estandarizacion", 3.55, 3.55, 3.0, C_AUD, [
    "npn  (enlaza con LA_Predio)", "nombre_original", "nit_original",
    "cond / destino / ph original"])

clase("U_Terreno", 11.55, 8.7, 4.1, C_TER, [
    "T_Id  (PK)", "predio_id  (FK)", "area_terreno_m2 / _ha", "[ GEOMETRIA poligono ]"])

clase("CR_UnidadConstruccion", 11.55, 6.55, 4.1, C_UC, [
    "T_Id  (PK)", "predio_id  (FK)", "numero_unidad",
    "num_habitaciones / num_banos", "num_locales / num_pisos",
    "estrato  (dom)", "destino_construccion_cod", "puntaje_calificacion",
    "area_construida_m2"])

clase("CR_ZonaHomogenea", 11.55, 3.55, 4.1, C_ZH, [
    "T_Id  (PK)", "predio_id  (FK)", "numero_segmento",
    "zona_fisica_cod", "zona_geoeconomica_cod", "area_terreno_m2"])

# --------------------------------------------------------------- RELACIONES
conecta("LA_Interesado", "right", "LA_Derecho", "left", "es titular de", "1 .. *")
conecta("LA_Predio", "top", "LA_Derecho", "bottom", "recae sobre", "1 .. *")
conecta("LA_FuenteAdministrativa", "right", "LA_Derecho", "bottom", "soporta", "1 .. *")
conecta("LA_Predio", "right", "U_Terreno", "left", "tiene terreno", "1 .. 1")
conecta("LA_Predio", "right", "CR_UnidadConstruccion", "left", "tiene construccion", "1 .. *")
conecta("LA_Predio", "right", "CR_ZonaHomogenea", "left", "tiene zona", "1 .. *")
conecta("LA_Predio", "left", "AUD_Estandarizacion", "right", "trazabilidad", "1 .. 1",
        color="#95a5a6")
# Procedencia (origen de los datos) en linea punteada
conecta("base de datos\ndepurada.shp", "bottom", "AUD_Estandarizacion", "left",
        "se estandariza ->", "", color="#b2babb", style=(0, (4, 3)))

# --------------------------------------------------------------- LEYENDA
ax.text(0.25, 1.18, "Convencion de llaves:  PK = T_Id (identificador LADM-COL)   ·   "
        "FK = referencia al T_Id del registro padre   ·   (dom) = campo con dominio (lista controlada)",
        ha="left", fontsize=8, color="#34495e")
ax.text(0.25, 0.88, "Alcance:  70 predios patrimoniales verificados  ·  1 interesado "
        "(antes ~24 variantes)  ·  55 unidades de construccion  ·  78 segmentos de zona homogenea",
        ha="left", fontsize=8, color="#34495e")

leyenda = [("LA_Interesado / Party", C_INT), ("LA_Derecho / RRR", C_DER),
           ("LA_Predio / BAUnit", C_PRE), ("LA_FuenteAdministrativa", C_FUE),
           ("U_Terreno / SpatialUnit", C_TER), ("CR_UnidadConstruccion", C_UC),
           ("CR_ZonaHomogenea", C_ZH), ("AUD_Estandarizacion", C_AUD)]
x0 = 0.25
for i, (txt, col) in enumerate(leyenda):
    cx = x0 + (i % 4) * 3.95
    cy = 0.50 - (i // 4) * 0.30
    ax.add_patch(Rectangle((cx, cy - 0.07), 0.22, 0.16, facecolor=col, edgecolor="none"))
    ax.text(cx + 0.30, cy, txt, ha="left", va="center", fontsize=7.4, color="#2c3e50")

plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
fig.savefig(OUT, dpi=130, facecolor="white", bbox_inches="tight")
print("Esquema generado:", OUT)
