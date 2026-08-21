# -*- coding: utf-8 -*-
# DIAGNOSTICO (no modifica nada). Pegar y ejecutar en la ventana de Python de ArcGIS Pro.
# Dime que imprime y con eso corrijo el script de carga.

import arcpy, os

CARPETA = r"C:\Users\nicol\Downloads\BASE_DATOS"          # <-- misma ruta que usaste
SHP_IN  = os.path.join(CARPETA, "base de datos depurada.shp")

print("1) Existe el shapefile?:", arcpy.Exists(SHP_IN), "->", SHP_IN)

# Campos y tipo del campo CODIGO
campos = {f.name: f.type for f in arcpy.ListFields(SHP_IN)}
print("2) Hay campo 'CODIGO'?:", "CODIGO" in campos, "| tipo:", campos.get("CODIGO"))
print("   Total de campos:", len(campos))

# Conteo total de registros
total = int(arcpy.management.GetCount(SHP_IN)[0])
print("3) Total de features en el shp:", total)

# Primeros 5 valores de CODIGO tal como los lee ArcGIS
print("4) Muestra de CODIGO (valor | tipo python | longitud):")
i = 0
muestra = []
with arcpy.da.SearchCursor(SHP_IN, ["CODIGO"]) as sc:
    for (cod,) in sc:
        muestra.append(cod)
        print("   ", repr(cod), "|", type(cod).__name__, "|", len(str(cod)) if cod is not None else 0)
        i += 1
        if i >= 5:
            break

# Cuantos coinciden con los 70 verificados
VERIFICADOS = {
    "880010100000002600017000000000","880010100000001230031000000000","880010100000002120007000000000",
    "880010100000002710001000000000","880010100000001610001000000000","880010100000001240030000000000",
}  # subconjunto de prueba (6 de los 70)
match = 0
with arcpy.da.SearchCursor(SHP_IN, ["CODIGO"]) as sc:
    for (cod,) in sc:
        if str(cod).strip() in VERIFICADOS:
            match += 1
print("5) Coincidencias con la muestra de 6 codigos:", match, "(si es 0 => el campo se lee distinto)")
print("\nListo. Copia y pegame TODO lo que imprimio.")
