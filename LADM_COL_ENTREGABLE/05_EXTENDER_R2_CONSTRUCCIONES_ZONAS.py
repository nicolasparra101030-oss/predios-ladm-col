# -*- coding: utf-8 -*-
# =============================================================================
#  EXTENSION DEL MODELO LADM-COL  ->  REGISTRO 2 (economico / fisico)
#  Construcciones (unidades) y Zonas Homogeneas (fisica y geoeconomica)
#
#  Predios patrimoniales - Departamento Archipielago de San Andres,
#  Providencia y Santa Catalina (NIT 892.400.038-2)
#
#  Modelo de referencia : Modelo Extendido Catastro-Registro LADM-COL V4.1
#                         clases CR_UnidadConstruccion / Zona Homogenea
#  Insumo               : "base de datos depurada.shp"  (campos R2_*)
#  Producto             : amplia  LADM_COL_Predios_Patrimoniales.gdb
#
#  QUE HACE
#    Agrega a la GDB existente, SIN tocar lo ya construido:
#      - Tabla  CR_UnidadConstruccion   (hasta 3 unidades por predio)
#      - Tabla  CR_ZonaHomogenea        (hasta 2 segmentos de terreno por predio)
#      - Dominios  dom_Estrato
#      - Relaciones  LA_Predio (1) -- (M) cada tabla nueva
#
#  REQUISITO
#    La GDB  LADM_COL_Predios_Patrimoniales.gdb  ya debe existir (la crea el
#    script 01).  Este script es ADITIVO e IDEMPOTENTE: si lo ejecutas otra vez
#    borra y vuelve a cargar solo estas dos tablas, sin alterar el resto.
#
#  COMO USARLO EN ARCGIS PRO
#    1. Ejecuta antes  01_CONSTRUIR_GDB_LADM_COL.py  (si aun no existe la GDB).
#    2. Abre ArcGIS Pro -> ventana de Python (o un Notebook).
#    3. Pega este script.  Verifica la variable CARPETA  (<-- EDITAR).
#    4. Ejecuta.
# =============================================================================

import arcpy, os, unicodedata

# ------------------------------------------------------------------ PARAMETROS
CARPETA  = r"C:\Users\nicol\Downloads\BASE_DATOS"          # <-- EDITAR ruta
SHP_IN   = os.path.join(CARPETA, "base de datos depurada.shp")
GDB      = os.path.join(CARPETA, "LADM_COL_Predios_Patrimoniales.gdb")
T_PRE    = os.path.join(GDB, "LA_Predio")

arcpy.env.overwriteOutput = True

if not arcpy.Exists(GDB):
    raise SystemExit("No existe la GDB. Ejecuta primero 01_CONSTRUIR_GDB_LADM_COL.py")
if not arcpy.Exists(T_PRE):
    raise SystemExit("No existe LA_Predio en la GDB. Reconstruye con el script 01.")

# ------------------------------------------------------- UTILIDADES DE LECTURA
import re
def _norm(s):
    # Empareja nombres de campo aunque la 'n' (de "Banos") venga codificada de
    # distintas formas: ArcGIS puede entregarla como 'n' (UTF-8) o como 'A+-'
    # (latin1, "Banos"). Se mapean ambos casos a 'n' antes de limpiar.
    s = (s or u"").lower()
    s = s.replace(u"ñ", u"n").replace(u"ã±", u"n")  # n-tilde y A-tilde+-
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9_]", "", s).strip()

def ni(v):
    # entero o None  (cuenta de habitaciones, banos, pisos, codigos de zona...)
    try:
        if v is None or v == "":
            return None
        return int(round(float(v)))
    except Exception:
        return None

def nd(v):
    # double >= 0  (areas)
    try:
        if v is None or v == "":
            return 0.0
        return round(float(v), 2)
    except Exception:
        return 0.0

# Resolver los nombres REALES de los campos del shp (R2_Banos lleva 'n' tilde)
_disp = [f.name for f in arcpy.ListFields(SHP_IN)]
_mapa = {_norm(n): n for n in _disp}
def campo(nombre_logico):
    real = _mapa.get(_norm(nombre_logico))
    if real is None:
        print("  [AVISO] No se encontro el campo:", nombre_logico)
    return real

# -------------------------------------------------- DEFINICION DE LOS GRUPOS R2
# Zonas homogeneas: hasta 2 segmentos de terreno (fisica, geoeconomica, area)
ZONAS = [
    (1, "R2_ZonaFis", "R2_ZonaEco", "R2_AreaTer"),
    (2, "R2_ZonaF_1", "R2_ZonaE_1", "R2_AreaT_1"),
]
# Construcciones: hasta 3 unidades  (habit, banos, locales, pisos, estrato,
#                                    destino, puntaje, area construida)
CONSTRUCCIONES = [
    (1, "R2_Habitac", "R2_Banos",   "R2_Locales", "R2_Pisos",   "R2_Estrato",
        "R2_Destino", "R2_Puntaje", "R2_AreaCon"),
    (2, "R2_Habit_1", "R2_Banos_",  "R2_Local_1", "R2_Pisos_1", "R2_Estra_1",
        "R2_Desti_1", "R2_Punta_1", "R2_AreaC_1"),
    (3, "R2_Habit_2", "R2_Bano_1",  "R2_Local_2", "R2_Pisos_2", "R2_Estra_2",
        "R2_Desti_2", "R2_Punta_2", "R2_AreaC_2"),
]

# =============================================================================
#  1) NPN de los 70 predios  ->  se leen de LA_Predio (no se duplica la lista)
# =============================================================================
npn_set = set()
with arcpy.da.SearchCursor(T_PRE, ["npn"]) as c:
    for (v,) in c:
        v = (v or "").strip()
        if v:
            npn_set.add(v)
print("Predios en LA_Predio:", len(npn_set))

# =============================================================================
#  2) LIMPIEZA IDEMPOTENTE  (borra relaciones y tablas si ya existian)
# =============================================================================
for rc in ["rc_Predio_UnidadConstruccion", "rc_Predio_ZonaHomogenea"]:
    p = os.path.join(GDB, rc)
    if arcpy.Exists(p):
        arcpy.management.Delete(p)
for t in ["CR_UnidadConstruccion", "CR_ZonaHomogenea"]:
    p = os.path.join(GDB, t)
    if arcpy.Exists(p):
        arcpy.management.Delete(p)

# =============================================================================
#  3) DOMINIO  dom_Estrato  (1..6)
# =============================================================================
dom_existentes = [d.name for d in arcpy.da.ListDomains(GDB)]
if "dom_Estrato" not in dom_existentes:
    arcpy.management.CreateDomain(GDB, "dom_Estrato",
                                  "Estrato socioeconomico", "SHORT", "CODED")
    for e in range(1, 7):
        arcpy.management.AddCodedValueToDomain(GDB, "dom_Estrato", e, "Estrato %d" % e)
    print("Dominio dom_Estrato creado.")

# =============================================================================
#  4) TABLAS NUEVAS
# =============================================================================
# 4.1  CR_UnidadConstruccion  (LA_BAUnit -> CR_UnidadConstruccion)
T_UC = os.path.join(GDB, "CR_UnidadConstruccion")
arcpy.management.CreateTable(GDB, "CR_UnidadConstruccion")
arcpy.management.AddField(T_UC, "T_Id", "TEXT", field_length=50)
arcpy.management.AddField(T_UC, "predio_id", "TEXT", field_length=40)   # = T_Id del predio (PRE_+npn)
arcpy.management.AddField(T_UC, "numero_unidad", "SHORT")               # 1,2,3 (orden IGAC)
arcpy.management.AddField(T_UC, "num_habitaciones", "SHORT")
arcpy.management.AddField(T_UC, "num_banos", "SHORT")
arcpy.management.AddField(T_UC, "num_locales", "SHORT")
arcpy.management.AddField(T_UC, "num_pisos", "SHORT")
arcpy.management.AddField(T_UC, "estrato", "SHORT")
arcpy.management.AddField(T_UC, "destino_construccion_cod", "SHORT")    # codigo IGAC numerico
arcpy.management.AddField(T_UC, "puntaje_calificacion", "LONG")
arcpy.management.AddField(T_UC, "area_construida_m2", "DOUBLE")
arcpy.management.AssignDomainToField(T_UC, "estrato", "dom_Estrato")

# 4.2  CR_ZonaHomogenea  (zona homogenea fisica y geoeconomica del terreno)
T_ZH = os.path.join(GDB, "CR_ZonaHomogenea")
arcpy.management.CreateTable(GDB, "CR_ZonaHomogenea")
arcpy.management.AddField(T_ZH, "T_Id", "TEXT", field_length=50)
arcpy.management.AddField(T_ZH, "predio_id", "TEXT", field_length=40)   # = T_Id del predio (PRE_+npn)
arcpy.management.AddField(T_ZH, "numero_segmento", "SHORT")             # 1,2
arcpy.management.AddField(T_ZH, "zona_fisica_cod", "SHORT")
arcpy.management.AddField(T_ZH, "zona_geoeconomica_cod", "SHORT")
arcpy.management.AddField(T_ZH, "area_terreno_m2", "DOUBLE")
print("Tablas CR_UnidadConstruccion y CR_ZonaHomogenea creadas.")

# =============================================================================
#  5) LEER EL SHAPEFILE  (solo los 70 predios)  Y ARMAR LAS FILAS
#     File GDB = una transaccion a la vez: primero se lee todo, luego se escribe.
# =============================================================================
cod = campo("CODIGO")
# Lista de campos a abrir en el cursor (resueltos a su nombre real)
logicos = ["CODIGO"]
for z in ZONAS:
    logicos += list(z[1:])
for u in CONSTRUCCIONES:
    logicos += list(u[1:])
reales = []
for lg in logicos:
    r = campo(lg)
    if r and r not in reales:
        reales.append(r)
idx = {r: i for i, r in enumerate(reales)}

def val(row, nombre_logico):
    r = campo(nombre_logico)
    return row[idx[r]] if (r in idx) else None

filas_uc, filas_zh = [], []
n_pred = 0
with arcpy.da.SearchCursor(SHP_IN, reales) as sc:
    for row in sc:
        npn = (row[idx[cod]] or "").strip()
        if npn not in npn_set:
            continue
        n_pred += 1

        # --- Zonas homogeneas ---
        for (slot, f_fis, f_eco, f_area) in ZONAS:
            zf = ni(val(row, f_fis))
            ze = ni(val(row, f_eco))
            ar = nd(val(row, f_area))
            if (zf or ze or ar > 0):     # solo segmentos con dato
                filas_zh.append(["ZH_%s_%d" % (npn, slot), "PRE_"+npn, slot, zf, ze, ar])

        # --- Unidades de construccion ---
        for (slot, f_h, f_b, f_l, f_p, f_e, f_d, f_pj, f_ac) in CONSTRUCCIONES:
            h  = ni(val(row, f_h));  b = ni(val(row, f_b));  l = ni(val(row, f_l))
            p  = ni(val(row, f_p));  e = ni(val(row, f_e));  d = ni(val(row, f_d))
            pj = ni(val(row, f_pj)); ac = nd(val(row, f_ac))
            # se carga la unidad solo si tiene algo fisico real
            if any(v for v in (h, b, l, p, ac)) or ac > 0:
                e = e if (e and 1 <= e <= 6) else None   # estrato valido o nulo
                filas_uc.append(["UC_%s_%d" % (npn, slot), "PRE_"+npn, slot,
                                 h, b, l, p, e, d, pj, ac])

print("Predios leidos:", n_pred,
      "| Unidades construccion:", len(filas_uc),
      "| Segmentos de zona:", len(filas_zh))

# =============================================================================
#  6) ESCRIBIR  (un cursor a la vez)
# =============================================================================
def cargar(destino, campos, filas):
    if not filas:
        return
    with arcpy.da.InsertCursor(destino, campos) as ic:
        for f in filas:
            ic.insertRow(f)

cargar(T_ZH, ["T_Id", "predio_id", "numero_segmento",
              "zona_fisica_cod", "zona_geoeconomica_cod", "area_terreno_m2"], filas_zh)
cargar(T_UC, ["T_Id", "predio_id", "numero_unidad",
              "num_habitaciones", "num_banos", "num_locales", "num_pisos",
              "estrato", "destino_construccion_cod", "puntaje_calificacion",
              "area_construida_m2"], filas_uc)
print("Datos cargados.")

# =============================================================================
#  7) RELACIONES  LA_Predio (1) -- (M) tabla nueva   (llave = npn)
# =============================================================================
# Convencion LADM-COL: la FK del hijo (predio_id) guarda el T_Id del predio.
arcpy.management.CreateRelationshipClass(
    T_PRE, T_UC, os.path.join(GDB, "rc_Predio_UnidadConstruccion"),
    "SIMPLE", "Tiene_unidad_construccion", "Pertenece_al_predio",
    "NONE", "ONE_TO_MANY", "NONE", "T_Id", "predio_id")
arcpy.management.CreateRelationshipClass(
    T_PRE, T_ZH, os.path.join(GDB, "rc_Predio_ZonaHomogenea"),
    "SIMPLE", "Tiene_zona_homogenea", "Pertenece_al_predio",
    "NONE", "ONE_TO_MANY", "NONE", "T_Id", "predio_id")
print("Relaciones creadas.")

print("\n========================================================")
print(" EXTENSION R2 LADM-COL completada:")
print("  + CR_UnidadConstruccion :", len(filas_uc), "unidades")
print("  + CR_ZonaHomogenea      :", len(filas_zh), "segmentos")
print("  Relacionadas 1--M con LA_Predio (llave npn)")
print("========================================================")
