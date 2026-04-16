#!/usr/bin/env python3
"""
generar_documentos.py
=====================
Llamado por n8n (Flujo A) para:
  1. Generar hojas de ruta PDF (1 por empleado)
  2. Generar albaranes PDF (1 por servicio)
  3. Guardar en /tmp/tagma/semana_XX/{Empleado}/

Uso: python3 generar_documentos.py '<JSON_planificacion>'
"""

import sys
import json
import os
import re

# Añadir directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plantillas import generar_hoja_ruta, generar_albaran, TIPO_SERVICIO

EMPLEADOS_DIR = {
    "Sergio Rodriguez":    "Sergio_Rodriguez",
    "Juan Carlos Jimenez": "Juan_Carlos_Jimenez",
    "Hafid Sabir":         "Hafid_Sabir",
    "Juan Adelson":        "Juan_Adelson",
}

DIAS_ES = {
    "lunes":     "LUNES",
    "martes":    "MARTES",
    "miercoles": "MIÉRCOLES",
    "jueves":    "JUEVES",
    "viernes":   "VIERNES",
}


def limpiar_nombre(texto: str) -> str:
    """Convierte texto a nombre de archivo seguro."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', texto)[:40]


def main():
    if len(sys.argv) < 2:
        print("ERROR: Se necesita el JSON de planificación como argumento.")
        sys.exit(1)

    # n8n puede pasar el JSON con comillas escapadas
    raw = sys.argv[1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR parseando JSON: {e}")
        sys.exit(1)

    # Puede venir envuelto en { plan: {...}, rutas: {...} }
    plan = data.get("plan", data)
    rutas = data.get("rutas", {})

    semana_num = plan.get("semana", 0)
    año = plan.get("año", 2026)
    fecha_lunes = plan.get("fecha_lunes", "")

    # Calcular label de semana
    emp_keys = list(plan.get("empleados", {}).keys())
    semana_label = fecha_lunes
    if emp_keys:
        # Intentar extraer viernes
        dias_emp = plan["empleados"][emp_keys[0]]
        fecha_viernes = ""
        for svc in dias_emp.get("viernes", []):
            if svc.get("fecha"):
                fecha_viernes = svc["fecha"]
                break
        if fecha_viernes:
            semana_label = f"{fecha_lunes} al {fecha_viernes}"

    # Directorio base
    base_dir = f"/tmp/tagma/semana_{semana_num}"
    os.makedirs(base_dir, exist_ok=True)

    archivos_generados = []

    for emp_nombre, dias in plan.get("empleados", {}).items():
        emp_dir_name = EMPLEADOS_DIR.get(emp_nombre, limpiar_nombre(emp_nombre))
        emp_dir = os.path.join(base_dir, emp_dir_name)
        os.makedirs(emp_dir, exist_ok=True)

        # ── Construir servicios_por_dia para la plantilla ──────────
        servicios_por_dia = {}
        for dia_en, dia_es in DIAS_ES.items():
            servicios_raw = dias.get(dia_en, [])
            servicios_por_dia[dia_es] = []
            for s in servicios_raw:
                servicios_por_dia[dia_es].append({
                    "fecha":            s.get("fecha", ""),
                    "hora_inicio":      s.get("hora_inicio", ""),
                    "hora_fin":         s.get("hora_fin", ""),
                    "llave":            s.get("llave", ""),
                    "personas":         s.get("personas", 1),
                    "duracion_h":       str(s.get("duracion_h", "")),
                    "desplazamiento_h": str(s.get("desplazamiento_h", "")),
                    "cliente":          s.get("cliente", ""),
                    "direccion":        s.get("direccion", ""),
                    "descripcion":      s.get("descripcion", s.get("observaciones", "")),
                    "tipo":             s.get("tipo", ""),
                    "frecuencia":       s.get("frecuencia", ""),
                    "observaciones":    s.get("observaciones", ""),
                })

        # Generar hoja de ruta
        hoja_path = os.path.join(emp_dir, f"HojaRuta_Semana{semana_num}_{emp_dir_name}.pdf")
        generar_hoja_ruta(
            empleado=emp_nombre,
            semana_label=semana_label,
            semana_num=semana_num,
            año=año,
            servicios_por_dia=servicios_por_dia,
            output_path=hoja_path
        )
        archivos_generados.append({"tipo": "hoja_ruta", "empleado": emp_nombre, "path": hoja_path})
        print(f"✓ Hoja ruta: {hoja_path}")

        # ── Generar albaranes ──────────────────────────────────────
        alb_counter = 1
        for dia_en, dia_es in DIAS_ES.items():
            for s in dias.get(dia_en, []):
                # ID albarán: año + semana + empleado (2 letras) + contador
                emp_code = "".join(w[0] for w in emp_nombre.split())[:3].upper()
                id_alb = f"{año}-S{semana_num:02d}-{emp_code}-{alb_counter:03d}"
                alb_counter += 1

                tipo_code = s.get("tipo", "")
                tipo_nombre = TIPO_SERVICIO.get(tipo_code, tipo_code)

                # Construir lista de tareas desde descripción
                desc = s.get("descripcion", "")
                tareas = [t.strip() for t in desc.split('.') if t.strip()][:4]
                if not tareas:
                    tareas = [desc] if desc else ["Ver descripción del servicio"]

                # Material
                material = []
                if s.get("material"):
                    material = [m.strip() for m in s["material"].split('·') if m.strip()]
                if s.get("maquinaria"):
                    material += [m.strip() for m in s["maquinaria"].split(',') if m.strip()]
                if not material:
                    material = ["Equipamiento estándar de servicio"]

                albaran_data = {
                    "id_albaran":   id_alb,
                    "fecha":        s.get("fecha", ""),
                    "cliente":      s.get("cliente", ""),
                    "direccion":    s.get("direccion", ""),
                    "poblacion":    s.get("poblacion", s.get("cp", "")),
                    "tipo_servicio": tipo_code,
                    "ambito":       s.get("ambito", ""),
                    "tareas":       tareas,
                    "material":     material,
                    "observaciones": s.get("observaciones", "") or s.get("obs_seguridad", ""),
                    "ejecucion": [{
                        "dia":         s.get("fecha", ""),
                        "tecnico":     emp_nombre,
                        "hora_inicio": s.get("hora_inicio", ""),
                        "hora_fin":    s.get("hora_fin", ""),
                        "tiempo_min":  "",
                    }],
                    "tecnico": emp_nombre,
                }

                cliente_safe = limpiar_nombre(s.get("cliente", "cliente"))[:25]
                alb_path = os.path.join(emp_dir, f"Albaran_{id_alb}_{cliente_safe}.pdf")
                generar_albaran(albaran_data, alb_path)
                archivos_generados.append({
                    "tipo": "albaran",
                    "empleado": emp_nombre,
                    "id_albaran": id_alb,
                    "path": alb_path
                })
                print(f"  ✓ Albarán: {alb_path}")

    # Resumen final en JSON (n8n puede leer stdout)
    resumen = {
        "ok": True,
        "semana": semana_num,
        "directorio_base": base_dir,
        "archivos": archivos_generados,
        "total_hojas_ruta": sum(1 for a in archivos_generados if a["tipo"] == "hoja_ruta"),
        "total_albaranes": sum(1 for a in archivos_generados if a["tipo"] == "albaran"),
    }
    print("\n" + json.dumps(resumen))


if __name__ == "__main__":
    main()
