"""Aplica los partidos extraídos de la web de la FFCM a datos.json y al Excel.

Uso:  python3 herramientas/aplicar.py extraido.json [AAAA-MM-DD]
  extraido.json  salida de herramientas/extractor.js (lista de partidos)
  AAAA-MM-DD     fecha de hoy para "actualizado" (opcional)

Imprime un resumen. Si no cambia nada, imprime "SIN CAMBIOS" y no toca los archivos.
"""
import json
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos.json"
EXCEL = RAIZ / "Clasificacion_Interescuelas_Alevin_G3.xlsx"
YO = "Sp. Cabanillas"


def norm(s):
    s = unicodedata.normalize("NFD", str(s).upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.replace('"', "").split())


def fecha_iso(f):
    return datetime.strptime(f, "%d-%m-%Y").strftime("%Y-%m-%d")


def main():
    extraido = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    hoy = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
    datos = json.loads(DATOS.read_text(encoding="utf-8"))

    idx = {(p["j"], norm(p["l"]), norm(p["v"])): p for p in datos["partidos"]}
    cambios, avisos, sin_acta = [], [], []
    extra = datos.setdefault("extra", {})

    for e in extraido:
        clave = (e["j"], norm(e["local"]), norm(e["visitante"]))
        p = idx.get(clave)
        if p is None:
            avisos.append(f"J{e['j']}: no encuentro {e['local']} - {e['visitante']} en el calendario")
            continue
        if e.get("fecha"):
            f = fecha_iso(e["fecha"])
            if p["f"] != f:
                p["f"] = f
        if e.get("marcador"):
            gl, gv = (int(x) for x in e["marcador"].split("-"))
            if (p.get("gl"), p.get("gv")) != (gl, gv):
                antes = "" if p.get("gl") is None else f" (antes {p['gl']}-{p['gv']})"
                cambios.append(f"J{p['j']}: {p['l']} {gl}-{gv} {p['v']}{antes}")
                p["gl"], p["gv"] = gl, gv
            if not e.get("acta"):
                sin_acta.append(f"J{p['j']}: {p['l']} {gl}-{gv} {p['v']}" + (" (equipo retirado)" if e.get("retirado") else ""))
        if YO in (p["l"], p["v"]) and p.get("gl") is None:
            nuevo = {"h": e.get("hora", ""), "c": e.get("campo", "")}
            if (nuevo["h"] or nuevo["c"]) and extra.get(str(p["j"])) != nuevo:
                extra[str(p["j"])] = nuevo

    # limpiar datos de hora/campo de partidos ya jugados
    for p in datos["partidos"]:
        if YO in (p["l"], p["v"]) and p.get("gl") is not None:
            extra.pop(str(p["j"]), None)

    jugadas = [p["j"] for p in datos["partidos"] if p.get("gl") is not None]
    datos["hasta_jornada"] = max(jugadas) if jugadas else 0

    for a in avisos:
        print("AVISO:", a)
    if not cambios:
        print("SIN CAMBIOS")
        return
    datos["actualizado"] = hoy
    DATOS.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    actualizar_excel(datos)

    print("CAMBIOS:")
    for c in cambios:
        print(" -", c)
    if sin_acta:
        print("SIN ACTA CERRADA (pueden cambiar):")
        for s in sin_acta:
            print(" -", s)
    print("PARTIDOS DEL CABANILLAS:")
    for p in sorted((p for p in datos["partidos"] if YO in (p["l"], p["v"]) and p.get("gl") is not None), key=lambda x: x["j"]):
        print(f" - J{p['j']}: {p['l']} {p['gl']}-{p['gv']} {p['v']}")


def actualizar_excel(datos):
    wb = openpyxl.load_workbook(EXCEL)
    ws, eq = wb["Calendario"], wb["Equipos"]

    def nombre(celda):
        ref = str(celda.value).replace("=Equipos!", "").replace("$", "")
        return eq[ref].value

    filas = {}
    for r in range(5, ws.max_row + 1):
        j = ws.cell(row=r, column=1).value
        if j:
            filas[(j, norm(nombre(ws.cell(row=r, column=3))), norm(nombre(ws.cell(row=r, column=6))))] = r
    for p in datos["partidos"]:
        r = filas.get((p["j"], norm(p["l"]), norm(p["v"])))
        if r is None:
            print("AVISO: fila de Excel no encontrada para", p["j"], p["l"], p["v"])
            continue
        ws.cell(row=r, column=2).value = datetime.strptime(p["f"], "%Y-%m-%d")
        if p.get("gl") is not None:
            ws.cell(row=r, column=4).value = p["gl"]
            ws.cell(row=r, column=5).value = p["gv"]
    wb.save(EXCEL)


if __name__ == "__main__":
    main()
