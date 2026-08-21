# -*- coding: utf-8 -*-
# =============================================================================
#  CONSTRUCCION DE FILE GEODATABASE EN MODELO LADM-COL
#  Predios patrimoniales - Departamento Archipielago de San Andres,
#  Providencia y Santa Catalina (NIT 892.400.038-2)
#
#  Modelo de referencia : Modelo Extendido Catastro-Registro LADM-COL V4.1
#                         apoyado en el Nucleo LADM-COL V4.0.1 (ICDE, Ac.002/2023)
#  Insumo               : "base de datos depurada.shp"
#  Alcance              : 70 predios verificados (propiedad del Departamento)
#
#  COMO USARLO EN ARCGIS PRO:
#    1. Abre ArcGIS Pro.  Pestana ANALISIS  ->  Python  (ventana de Python),
#       o  Catalogo -> clic derecho en una carpeta -> Nuevo -> Notebook.
#    2. Pega este script.
#    3. Cambia UNICAMENTE la variable CARPETA (linea marcada con  <-- EDITAR).
#    4. Ejecuta.  Se creara  LADM_COL_Predios_Patrimoniales.gdb
# =============================================================================

import arcpy, os

# ------------------------------------------------------------------ PARAMETROS
CARPETA   = r"C:\Users\nicol\Downloads\BASE_DATOS"          # <-- EDITAR ruta
SHP_IN    = os.path.join(CARPETA, "base de datos depurada.shp")
GDB_NAME  = "LADM_COL_Predios_Patrimoniales.gdb"
GDB       = os.path.join(CARPETA, GDB_NAME)
SOBRESCRIBIR = True   # True = borra y reconstruye la GDB si ya existe

arcpy.env.overwriteOutput = True

# ------------------------------------------------------- CONSTANTES DE NORMALIZACION
NOMBRE_CANON = u"DEPARTAMENTO ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA"
NIT_CANON    = u"892400038-2"

# Destino economico IGAC (codigo en letra). Los marcados POR VALIDAR deben
# confirmarse contra la tabla del IGAC vigente del origen de los datos.
DESTINO = {
    u"A": u"Habitacional", u"B": u"Industrial", u"C": u"Comercial",
    u"E": u"Minero", u"F": u"Cultural", u"G": u"Recreacional",
    u"H": u"Salubridad", u"I": u"Institucional", u"J": u"Educativo",
    u"D": u"Agropecuario (POR VALIDAR IGAC)", u"K": u"Religioso (POR VALIDAR IGAC)",
    u"P": u"Uso publico (POR VALIDAR IGAC)", u"R": u"Servicios especiales (POR VALIDAR IGAC)",
    u"S": u"Servicios (POR VALIDAR IGAC)", u"": u"Sin dato",
}

# 70 numeros prediales nacionales verificados (propiedad del Departamento)
VERIFICADOS = {
    "880010100000002600017000000000", "880010100000001230031000000000", "880010100000002120007000000000",
    "880010100000002120024000000000", "880010100000002710001000000000", "880010100000001610001000000000",
    "880010100000001240030000000000", "880010100000001660019000000000", "880010100000001420093000000000",
    "880010100000002280071000000000", "880010100000000400002000000000", "880010100000000410010000000000",
    "880010100000000670002000000000", "880010100000000870006000000000", "880010100000000190019000000000",
    "880010100000000710007000000000", "880010100000000760006000000000", "880010100000000140001000000000",
    "880010100000000360163000000000", "880010100000000190017000000000", "880010100000000670015000000000",
    "880010100000000350014000000000", "880010100000000120003000000000", "880010100000000150001000000000",
    "880010100000000640017000000000", "880010100000000130001000000000", "880010100000001550001000000000",
    "880010100000000120002000000000", "880010100000000260024000000000", "880010100000000100021000000000",
    "880010100000000840003000000000", "880010100000000190016000000000", "880010100000000030002000000000",
    "880010100000000150002000000000", "880010000000000140360000000000", "880010000000000130121000000000",
    "880010000000000130098000000000", "880010000000000130096000000000", "880010000000000130097000000000",
    "880010000000000130094000000000", "880010000000000130095000000000", "880010000000000130099000000000",
    "880010000000000130082000000000", "880010000000000130084000000000", "880010000000000130088000000000",
    "880010000000000130080000000000", "880010000000000100377000000000", "880010002000000070075000000000",
    "880010002000000120046000000000", "880010000000000142128000000000", "880010000000000120893000000000",
    "880010002000000110002000000000", "880010000000000040842000000000", "880010000000000030054000000000",
    "880010000000000070072000000000", "880010000000000070018000000000", "880010000000000070346000000000",
    "880010000000000010011000000000", "880010000000000010452000000000", "880010000000000011064000000000",
    "880010002000000030004000000000", "880010002000000060021000000000", "880010002000000030005000000000",
    "880010000000000010928000000000", "880010000000000010126000000000", "880010000000000140819000000000",
    "880010000000000142493000000000", "880010000000000060310000000000", "880010000000000010211000000000",
    "880010000000000130089000000000",
}

# ------------------------------------------------------------ FUNCIONES LIMPIEZA
import unicodedata
def _sin_acentos(v):
    # Quita acentos y caracteres mal codificados (ej. "Publico"/"P?blico" -> "publico")
    v = (v or u"").replace(u"�", u"")
    v = unicodedata.normalize("NFKD", v).encode("ascii", "ignore").decode("ascii")
    return v.strip().lower()

def limpiar_cond(v):
    v = _sin_acentos(v)
    if v.startswith(u"pu"): return u"Bien_Uso_Publico"
    if v.startswith(u"pr"): return u"Bien_Fiscal"
    return u"Sin_dato"

def limpiar_ph(v):
    v = _sin_acentos(v)
    if v.startswith(u"s"): return u"Si"
    if v.startswith(u"n"): return u"No"
    return u""

def num(v):
    try: return float(v)
    except: return 0.0

# =============================================================================
#  1) CREAR LA GEODATABASE
# =============================================================================
if arcpy.Exists(GDB):
    if SOBRESCRIBIR:
        arcpy.management.Delete(GDB)
    else:
        raise SystemExit("La GDB ya existe y SOBRESCRIBIR=False")
arcpy.management.CreateFileGDB(CARPETA, GDB_NAME)
print("GDB creada:", GDB)

sr = arcpy.Describe(SHP_IN).spatialReference   # MAGNA-SIRGAS Origen Nacional
print("Sistema de referencia:", sr.name)

# =============================================================================
#  2) DOMINIOS (listas controladas LADM-COL)
# =============================================================================
def dominio(nombre, descripcion, valores):
    arcpy.management.CreateDomain(GDB, nombre, descripcion, "TEXT", "CODED")
    for cod, desc in valores:
        arcpy.management.AddCodedValueToDomain(GDB, nombre, cod, desc)

dominio("dom_TipoInteresado", "Tipo de interesado (LA_Interesado)", [
    ("Persona_Natural", "Persona Natural"), ("Persona_Juridica", "Persona Juridica"),
    ("Grupo_Interesados", "Grupo de Interesados")])
dominio("dom_TipoDocumento", "Tipo de documento de identidad", [
    ("Cedula_Ciudadania", "Cedula de Ciudadania"), ("NIT", "NIT"),
    ("Cedula_Extranjeria", "Cedula de Extranjeria"), ("Pasaporte", "Pasaporte"),
    ("Sin_Identificacion", "Sin Identificacion")])
dominio("dom_TipoDerecho", "Tipo de derecho (LA_Derecho / RRR)", [
    ("Dominio", "Dominio / Propiedad"), ("Posesion", "Posesion"),
    ("Ocupacion", "Ocupacion"), ("Tenencia", "Tenencia")])
dominio("dom_CondicionPredio", "Condicion del predio patrimonial", [
    ("Bien_Uso_Publico", "Bien de Uso Publico"), ("Bien_Fiscal", "Bien Fiscal (patrimonial)"),
    ("Sin_dato", "Sin dato")])
dominio("dom_TipoFuente", "Tipo de fuente administrativa", [
    ("Matricula_Inmobiliaria", "Matricula Inmobiliaria"),
    ("Escritura_Publica", "Escritura Publica"), ("Acto_Administrativo", "Acto Administrativo"),
    ("Sin_dato", "Sin dato")])
dominio("dom_SiNo", "Si / No", [("Si", "Si"), ("No", "No")])
dominio("dom_DestinoEconomico", "Destinacion economica (codigo IGAC en letra)",
        sorted([(k, v) for k, v in DESTINO.items() if k]))
print("Dominios creados.")

# =============================================================================
#  3) FEATURE CLASS  (Unidad espacial: terreno - poligono)
# =============================================================================
FC_TER = os.path.join(GDB, "U_Terreno")
arcpy.management.CreateFeatureclass(GDB, "U_Terreno", "POLYGON", spatial_reference=sr)
arcpy.management.AddField(FC_TER, "T_Id", "TEXT", field_length=40)
arcpy.management.AddField(FC_TER, "predio_id", "TEXT", field_length=40)
arcpy.management.AddField(FC_TER, "area_terreno_m2", "DOUBLE")
arcpy.management.AddField(FC_TER, "area_terreno_ha", "DOUBLE")

# =============================================================================
#  4) TABLAS LADM-COL
# =============================================================================
def tabla(nombre, campos):
    ruta = os.path.join(GDB, nombre)
    arcpy.management.CreateTable(GDB, nombre)
    for nm, tipo, ln in campos:
        if tipo == "TEXT": arcpy.management.AddField(ruta, nm, "TEXT", field_length=ln)
        else: arcpy.management.AddField(ruta, nm, tipo)
    return ruta

T_INT = tabla("LA_Interesado", [
    ("T_Id","TEXT",40),("tipo_interesado","TEXT",30),("tipo_documento","TEXT",30),
    ("numero_documento","TEXT",30),("nombre","TEXT",255)])
T_PRE = tabla("LA_Predio", [
    ("T_Id","TEXT",40),("npn","TEXT",30),("codigo_anterior","TEXT",25),
    ("tipo_predio","TEXT",20),("condicion_predio","TEXT",25),
    ("destino_economico_cod","TEXT",4),("destino_economico","TEXT",60),
    ("propiedad_horizontal","TEXT",4),
    ("area_terreno_geom_m2","DOUBLE",0),("area_terreno_ha","DOUBLE",0),
    ("area_registral_m2","DOUBLE",0),("area_construida_m2","DOUBLE",0),
    ("avaluo_catastral","DOUBLE",0),("direccion","TEXT",255),
    ("matricula_inmobiliaria","TEXT",25)])
T_DER = tabla("LA_Derecho", [
    ("T_Id","TEXT",40),("tipo_derecho","TEXT",20),
    ("interesado_id","TEXT",40),("predio_id","TEXT",40),("fuente_id","TEXT",40)])
T_FUE = tabla("LA_FuenteAdministrativa", [
    ("T_Id","TEXT",40),("tipo_fuente","TEXT",30),("numero","TEXT",25),
    ("ente_emisor","TEXT",60)])
# Tabla de auditoria: conserva el valor ORIGINAL para trazabilidad
T_AUD = tabla("AUD_Estandarizacion", [
    ("npn","TEXT",30),("nombre_original","TEXT",255),("nit_original","TEXT",30),
    ("cond_original","TEXT",30),("destino_original","TEXT",10),("ph_original","TEXT",10)])
print("Tablas creadas.")

# =============================================================================
#  5) ASIGNAR DOMINIOS
# =============================================================================
arcpy.management.AssignDomainToField(T_INT, "tipo_interesado", "dom_TipoInteresado")
arcpy.management.AssignDomainToField(T_INT, "tipo_documento",  "dom_TipoDocumento")
arcpy.management.AssignDomainToField(T_PRE, "condicion_predio","dom_CondicionPredio")
arcpy.management.AssignDomainToField(T_PRE, "destino_economico_cod", "dom_DestinoEconomico")
arcpy.management.AssignDomainToField(T_PRE, "propiedad_horizontal",  "dom_SiNo")
arcpy.management.AssignDomainToField(T_DER, "tipo_derecho",    "dom_TipoDerecho")
arcpy.management.AssignDomainToField(T_FUE, "tipo_fuente",     "dom_TipoFuente")
print("Dominios asignados.")

# =============================================================================
#  6) CARGAR DATOS (lee el shapefile, filtra y estandariza)
# =============================================================================
# 6.1 Interesado unico (antes ~24 variantes, ahora 1)
with arcpy.da.InsertCursor(T_INT, ["T_Id","tipo_interesado","tipo_documento",
                                   "numero_documento","nombre"]) as ic:
    ic.insertRow(["INT_DPTO_88","Persona_Juridica","NIT",NIT_CANON,NOMBRE_CANON])

campos_in = ["CODIGO","CODIGO_ANT","Cond","R1_Destino","PH","R1_AreaTer",
             "R1_AreaCon","R1_Avaluo","R1_Direcci","R2_Matricu","R1_Nombre",
             "R1_NoDocum","SHAPE@","SHAPE@AREA"]

# 6.2 Primero LEER el shapefile y acumular las filas en memoria.
#     Importante: una File GDB solo admite UNA transaccion de edicion a la vez,
#     por eso NO se abren varios InsertCursor simultaneos (eso causa el error
#     "workspace already in transaction mode"). Se lee todo y luego se escribe
#     cada tabla por separado, con un solo cursor abierto a la vez.
filas_ter, filas_pre, filas_der, filas_fue, filas_aud = [], [], [], [], []
fuentes_creadas = set()
n = 0
with arcpy.da.SearchCursor(SHP_IN, campos_in) as sc:
    for row in sc:
        (npn, codant, cond, dest, ph, aterr, acon, avaluo, direc,
         matr, nom_o, nit_o, shape, area_m2) = row
        npn = (npn or "").strip()
        if npn not in VERIFICADOS:
            continue
        cond_e = limpiar_cond(cond)
        dest = (dest or "").strip()
        dest_desc = DESTINO.get(dest, u"POR VALIDAR IGAC")
        matr = (matr or "").strip()
        area_m2 = round(area_m2 or 0.0, 2)
        area_ha = round((area_m2 or 0.0) / 10000.0, 4)

        # predio_id (FK) guarda el T_Id del predio = "PRE_"+npn  (convencion LADM-COL:
        # toda llave foranea referencia el T_Id del registro padre)
        filas_ter.append([shape, "TER_"+npn, "PRE_"+npn, area_m2, area_ha])
        filas_pre.append(["PRE_"+npn, npn, (codant or "").strip(),
            "Privado" if cond_e == "Bien_Fiscal" else "Publico",
            cond_e, dest, dest_desc, limpiar_ph(ph),
            area_m2, area_ha, num(aterr), num(acon), num(avaluo),
            (direc or "").strip(), matr])

        fue_id = ""
        if matr:
            fue_id = "FUE_"+matr
            if fue_id not in fuentes_creadas:
                fuentes_creadas.add(fue_id)
                filas_fue.append([fue_id,"Matricula_Inmobiliaria",matr,"ORIP 450 - San Andres"])
        filas_der.append(["DER_"+npn,"Dominio","INT_DPTO_88","PRE_"+npn,fue_id])
        filas_aud.append([npn,(nom_o or "").strip(),(nit_o or "").strip(),
            (cond or "").replace(u"�",u"u"),dest,(ph or "").replace(u"�",u"i")])
        n += 1

# 6.3 Ahora ESCRIBIR cada tabla por separado (un cursor a la vez, en bloque
#     'with' para que se libere y confirme aunque algo falle).
def cargar(tabla_dest, campos, filas):
    if not filas:
        return
    with arcpy.da.InsertCursor(tabla_dest, campos) as ic:
        for f in filas:
            ic.insertRow(f)

cargar(FC_TER, ["SHAPE@","T_Id","predio_id","area_terreno_m2","area_terreno_ha"], filas_ter)
cargar(T_PRE, ["T_Id","npn","codigo_anterior","tipo_predio",
        "condicion_predio","destino_economico_cod","destino_economico","propiedad_horizontal",
        "area_terreno_geom_m2","area_terreno_ha","area_registral_m2","area_construida_m2",
        "avaluo_catastral","direccion","matricula_inmobiliaria"], filas_pre)
cargar(T_DER, ["T_Id","tipo_derecho","interesado_id","predio_id","fuente_id"], filas_der)
cargar(T_FUE, ["T_Id","tipo_fuente","numero","ente_emisor"], filas_fue)
cargar(T_AUD, ["npn","nombre_original","nit_original",
        "cond_original","destino_original","ph_original"], filas_aud)
print("Predios cargados:", n, "| Fuentes (matriculas):", len(fuentes_creadas))

# =============================================================================
#  7) RELATIONSHIP CLASSES (relaciones del modelo)
#     Llave: origin_primary_key = T_Id del padre  <->  origin_foreign_key del hijo.
#     Todas las FK (predio_id, interesado_id, fuente_id) almacenan el T_Id del
#     padre, por lo que las relaciones enlazan registros correctamente.
# =============================================================================
def rel(nombre, origen, destino, fk_label, ok, dk, card):
    arcpy.management.CreateRelationshipClass(
        origen, destino, os.path.join(GDB,nombre),
        "SIMPLE", fk_label, "Pertenece_a", "NONE", card, "NONE", ok, dk)

# Predio (1) -- (1) Terreno
rel("rc_Predio_Terreno", T_PRE, FC_TER, "Tiene_terreno", "T_Id", "predio_id", "ONE_TO_ONE")
# Predio (1) -- (M) Derecho
rel("rc_Predio_Derecho", T_PRE, T_DER, "Tiene_derecho", "T_Id", "predio_id", "ONE_TO_MANY")
# Interesado (1) -- (M) Derecho
rel("rc_Interesado_Derecho", T_INT, T_DER, "Es_titular_de", "T_Id", "interesado_id", "ONE_TO_MANY")
# Fuente (1) -- (M) Derecho
rel("rc_Fuente_Derecho", T_FUE, T_DER, "Soporta", "T_Id", "fuente_id", "ONE_TO_MANY")
print("Relaciones creadas.")

print("\n========================================================")
print(" GDB LADM-COL construida con exito:")
print(" ", GDB)
print(" Feature class: U_Terreno  |  Tablas: LA_Predio, LA_Interesado,")
print("  LA_Derecho, LA_FuenteAdministrativa, AUD_Estandarizacion")
print("========================================================")
