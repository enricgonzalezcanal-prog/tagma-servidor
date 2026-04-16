"""
plantillas.py
=============
Módulo de generación de PDFs para el agente de planificación TAGMA.

Funciones públicas:
    generar_albaran(data, output_path)
    generar_hoja_ruta(empleado, semana_label, semana_num, año,
                      servicios_por_dia, output_path)

Cada albarán → 1 PDF.
Cada empleado → 1 PDF con su hoja de ruta semanal completa.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

W, H = A4

# ── Colores corporativos ──────────────────────────────────────────
TEAL       = colors.HexColor("#1B7A8C")
TEAL_LIGHT = colors.HexColor("#E8F4F6")
TEAL_MED   = colors.HexColor("#D0E8EC")
GRAY_DARK  = colors.HexColor("#333333")
GRAY_MID   = colors.HexColor("#666666")
GRAY_LIGHT = colors.HexColor("#F5F5F5")
GRAY_LINE  = colors.HexColor("#DDDDDD")
ORANGE     = colors.HexColor("#E8820C")
ORANGE_L   = colors.HexColor("#FEF0E0")
WHITE      = colors.white

LOGO_PATH  = "/Users/enric/TAGMA/agente/logo.jpg"
LOGO_H_MM  = 16
LOGO_W_MM  = LOGO_H_MM * (1337 / 747)   # 28.6 mm

DIAS = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]

# ── Tablas de códigos ─────────────────────────────────────────────
TIPO_SERVICIO = {
    "AB":  "Abrillantado / Vitrificado",
    "LC":  "Limpieza de Cristales",
    "FD":  "Realización de Fondos",
    "LE":  "Limpiezas Especiales",
    "RF":  "Revisión / Fondo periódico",
    "LG":  "Limpieza General",
    "A":   "Actuación puntual",
    "C":   "Cuatrimestral (servicio)",
}

FRECUENCIA = {
    "S":   "Semanal",
    "Q":   "Quincenal",
    "M":   "Mensual",
    "B":   "Bimestral",
    "T":   "Trimestral",
    "C":   "Cuatrimestral",
    "SM":  "Semestral",
    "A":   "Anual",
    "BA":  "Bianual",
}


# ═════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════

def _logo_header(c, y_top, right_block_fn=None):
    """Dibuja la cabecera teal con logo. Devuelve y inferior del header."""
    header_h = 26 * mm
    c.setFillColor(TEAL)
    c.rect(0, y_top - header_h, W, header_h, fill=1, stroke=0)

    # Logo en recuadro blanco
    c.setFillColor(WHITE)
    c.rect(10*mm, y_top - header_h + 3*mm,
           LOGO_W_MM*mm + 4*mm, LOGO_H_MM*mm + 4*mm, fill=1, stroke=0)
    c.drawImage(LOGO_PATH, 12*mm, y_top - header_h + 5*mm,
                width=LOGO_W_MM*mm, height=LOGO_H_MM*mm,
                preserveAspectRatio=True, mask='auto')

    if right_block_fn:
        right_block_fn(c, y_top, header_h)

    return y_top - header_h


def _footer(c):
    c.setFillColor(TEAL)
    c.rect(0, 0, W, 8*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(W / 2, 2.8*mm, "Grupo ServiCare · enric@servicare.net")


def _section_bar(c, y, label):
    """Barra teal con etiqueta centrada. Devuelve y inferior."""
    c.setFillColor(TEAL)
    c.rect(12*mm, y - 7*mm, W - 24*mm, 7*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(W / 2, y - 4*mm, label)
    return y - 7*mm


def _box(c, y, height, fill=None):
    """Rectángulo con borde gris suave."""
    bg = fill if fill else GRAY_LIGHT
    c.setFillColor(bg)
    c.rect(12*mm, y - height, W - 24*mm, height, fill=1, stroke=0)
    c.setStrokeColor(GRAY_LINE)
    c.setLineWidth(0.5)
    c.rect(12*mm, y - height, W - 24*mm, height, fill=0, stroke=1)
    return y - height


# ═════════════════════════════════════════════════════════════════
# ALBARÁN
# ═════════════════════════════════════════════════════════════════

def generar_albaran(data: dict, output_path: str):
    """
    data keys:
        id_albaran, fecha, cliente, direccion, poblacion,
        tipo_servicio (código, p.ej. "LC"),
        ambito, tareas (list[str]), material (list[str]),
        observaciones (str), ejecucion (list[dict]),
        tecnico (str)

    ejecucion item keys: dia, tecnico, hora_inicio, hora_fin, tiempo_min
    """
    c = rl_canvas.Canvas(output_path, pagesize=A4)

    # ── Header ──────────────────────────────────────────────────
    def _right(c, y_top, hh):
        c.setFillColor(TEAL)
        c.roundRect(W - 75*mm, y_top - hh + 3*mm, 63*mm, hh - 6*mm, 4,
                    fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica", 7)
        c.drawCentredString(W - 43.5*mm, y_top - 10*mm, "ALBARÁN DE SERVICIO")
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(W - 43.5*mm, y_top - 17*mm, data["id_albaran"])
        c.setFont("Helvetica", 7)
        c.drawCentredString(W - 43.5*mm, y_top - 22*mm, f"Fecha: {data['fecha']}")

    y = _logo_header(c, H, _right)

    # Separador
    c.setStrokeColor(TEAL); c.setLineWidth(1.5)
    c.line(12*mm, y - 2*mm, W - 12*mm, y - 2*mm)
    y -= 8*mm

    # ── Campos ──────────────────────────────────────────────────
    tipo_code = data.get("tipo_servicio", "")
    tipo_full = f"{tipo_code} — {TIPO_SERVICIO.get(tipo_code, tipo_code)}"

    fields = [
        ("Cliente",            data.get("cliente", "")),
        ("Dirección servicio", data.get("direccion", "")),
        ("Población",          data.get("poblacion", "")),
        ("Tipo de servicio",   tipo_full),
        ("Ámbito actuación",   data.get("ambito", "")),
    ]
    LBL_W = 46 * mm
    for label, value in fields:
        c.setFillColor(TEAL);      c.setFont("Helvetica-Bold", 8)
        c.drawString(12*mm, y, label)
        c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 9)
        # Truncar si es muy largo para no salirse
        val = value
        if len(val) > 70:
            val = val[:70] + "…"
        c.drawString(12*mm + LBL_W, y, val)
        c.setStrokeColor(GRAY_LINE); c.setLineWidth(0.5)
        c.line(12*mm, y - 2.5*mm, W - 12*mm, y - 2.5*mm)
        y -= 8.5*mm

    # ── Tareas ──────────────────────────────────────────────────
    y -= 2*mm
    y = _section_bar(c, y, "TAREAS A REALIZAR")
    box_h = max(len(data.get("tareas", [])) * 5.5*mm + 8*mm, 28*mm)
    _box(c, y, box_h)
    ty = y - 5*mm
    c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 8.5)
    for line in data.get("tareas", []):
        c.drawString(16*mm, ty, f"• {line}")
        ty -= 5.5*mm
    y -= box_h + 3*mm

    # ── Material ────────────────────────────────────────────────
    y = _section_bar(c, y, "MAQUINARIA Y PRODUCTOS UTILIZADOS")
    box_h = max(len(data.get("material", [])) * 5.5*mm + 8*mm, 20*mm)
    _box(c, y, box_h)
    ty = y - 5*mm
    c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 8.5)
    for mat in data.get("material", []):
        c.drawString(16*mm, ty, f"• {mat}")
        ty -= 5.5*mm
    y -= box_h + 3*mm

    # ── Observaciones ───────────────────────────────────────────
    y = _section_bar(c, y, "OBSERVACIONES DE SEGURIDAD")
    obs_text = data.get("observaciones", "Sin observaciones específicas.")
    # Wrap manual: max ~95 chars per line at font 8.5
    def _wrap(text, max_ch=92):
        words = text.split()
        lines, line = [], ""
        for w in words:
            if len(line) + len(w) + 1 <= max_ch:
                line = (line + " " + w).strip()
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
        return lines
    obs_lines = _wrap(obs_text)
    box_h = max(len(obs_lines) * 5.5*mm + 8*mm, 14*mm)
    _box(c, y, box_h)
    ty = y - 5.5*mm
    c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 8.5)
    for ol in obs_lines:
        c.drawString(16*mm, ty, ol)
        ty -= 5.5*mm
    y -= box_h + 3*mm

    # ── Tabla ejecución ─────────────────────────────────────────
    y = _section_bar(c, y, "DATOS DE EJECUCIÓN")

    # Cols: dia(40) tecnico(65) h_inicio(28) h_fin(28) minutos(rest)
    COLS = [
        (12*mm,  40*mm, "Día"),
        (54*mm,  65*mm, "Técnico"),
        (121*mm, 28*mm, "Hora inicio"),
        (151*mm, 28*mm, "Hora fin"),
        (181*mm, W - 12*mm - 181*mm, "Tiempo (min)"),
    ]
    ROW_H = 7*mm

    # Header
    c.setFillColor(TEAL_MED)
    c.rect(12*mm, y - ROW_H, W - 24*mm, ROW_H, fill=1, stroke=0)
    c.setStrokeColor(GRAY_LINE); c.setLineWidth(0.4)
    c.rect(12*mm, y - ROW_H, W - 24*mm, ROW_H, fill=0, stroke=1)
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 8)
    for x, _w, lbl in COLS:
        c.drawString(x + 1.5*mm, y - 4.5*mm, lbl)
    y -= ROW_H

    for row in data.get("ejecucion", [{}]):
        c.setFillColor(WHITE)
        c.rect(12*mm, y - ROW_H, W - 24*mm, ROW_H, fill=1, stroke=0)
        c.setStrokeColor(GRAY_LINE); c.setLineWidth(0.4)
        c.rect(12*mm, y - ROW_H, W - 24*mm, ROW_H, fill=0, stroke=1)
        c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 8)
        vals = [row.get("dia",""), row.get("tecnico",""),
                row.get("hora_inicio",""), row.get("hora_fin",""),
                row.get("tiempo_min","")]
        for (x, _w, _), v in zip(COLS, vals):
            c.drawString(x + 1.5*mm, y - 4.5*mm, v)
        y -= ROW_H

    # ── Firmas ──────────────────────────────────────────────────
    firma_y = 28*mm
    bw, bh = 76*mm, 24*mm

    # Técnico (izquierda)
    c.setFillColor(TEAL_LIGHT)
    c.rect(12*mm, firma_y, bw, bh, fill=1, stroke=0)
    c.setStrokeColor(TEAL); c.setLineWidth(0.8)
    c.rect(12*mm, firma_y, bw, bh, fill=0, stroke=1)
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(14*mm, firma_y + bh - 5*mm, "Fdo. Técnico")
    c.setFillColor(GRAY_MID); c.setFont("Helvetica", 7)
    c.drawString(14*mm, firma_y + 4*mm, data.get("tecnico", ""))

    # Cliente (derecha)
    rx = W - 12*mm - bw
    c.setFillColor(TEAL_LIGHT)
    c.rect(rx, firma_y, bw, bh, fill=1, stroke=0)
    c.setStrokeColor(TEAL); c.setLineWidth(0.8)
    c.rect(rx, firma_y, bw, bh, fill=0, stroke=1)
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(rx + 2*mm, firma_y + bh - 5*mm, "Fdo. Cliente")
    c.setFillColor(GRAY_MID); c.setFont("Helvetica", 7)
    c.drawString(rx + 2*mm, firma_y + 12*mm, "Nombre: _______________________")
    c.drawString(rx + 2*mm, firma_y + 5*mm,  "DNI:      _______________________")

    _footer(c)
    c.save()


# ═════════════════════════════════════════════════════════════════
# HOJA DE RUTA SEMANAL
# ═════════════════════════════════════════════════════════════════

def generar_hoja_ruta(empleado: str, semana_label: str, semana_num: int,
                      año: int, servicios_por_dia: dict, output_path: str):
    """
    servicios_por_dia: { "LUNES": [...], "MARTES": [...], ... }
    cada servicio:
        fecha, hora_inicio, hora_fin, llave, personas (int),
        duracion_h (str/float), desplazamiento_h (str/float),
        cliente, direccion, descripcion,
        tipo (código), frecuencia (código), observaciones
    """
    c = rl_canvas.Canvas(output_path, pagesize=A4)

    # ── Header ──────────────────────────────────────────────────
    def _right(c, y_top, hh):
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(W - 12*mm, y_top - 10*mm,
                          f"HOJA DE RUTA — SEMANA {semana_num} / {año}")
        c.setFont("Helvetica", 8)
        c.drawRightString(W - 12*mm, y_top - 17*mm, f"Técnico: {empleado}")
        c.drawRightString(W - 12*mm, y_top - 22*mm, semana_label)

    y = _logo_header(c, H, _right)

    # ── Resumen ─────────────────────────────────────────────────
    total_svc = sum(len(v) for v in servicios_por_dia.values())
    total_h   = sum(
        float(s.get("duracion_h", 0)) + float(s.get("desplazamiento_h", 0))
        for v in servicios_por_dia.values() for s in v)
    svc_2p = sum(int(s.get("personas", 1)) >= 2
                 for v in servicios_por_dia.values() for s in v)

    ry = y - 2*mm
    c.setFillColor(TEAL_LIGHT)
    c.rect(12*mm, ry - 9*mm, W - 24*mm, 9*mm, fill=1, stroke=0)
    c.setStrokeColor(TEAL); c.setLineWidth(0.6)
    c.rect(12*mm, ry - 9*mm, W - 24*mm, 9*mm, fill=0, stroke=1)

    items = [
        ("Servicios semana",   str(total_svc)),
        ("Horas estimadas",    f"{total_h:.1f} h"),
        ("Servicios 2 pers.",  str(svc_2p)),
        ("OBLIGATORIO",        "Albarán firmado + DNI / nombre legible"),
    ]
    step = (W - 24*mm) / len(items)
    for i, (lbl, val) in enumerate(items):
        x = 14*mm + i * step
        c.setFillColor(GRAY_MID); c.setFont("Helvetica", 6)
        c.drawString(x, ry - 3.5*mm, lbl)
        c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 7.5)
        c.drawString(x, ry - 7.5*mm, val)
    y = ry - 13*mm

    # ── Columnas de servicios ────────────────────────────────────
    # Usable width: 12mm→198mm = 186mm
    # hi(14) hf(14) llave(11) pers(9) dur(11) dsp(11) cli(72) tipo(14) obs(30) = 186mm
    CX = dict(hi=12, hf=26, llave=40, pers=51, dur=60, dsp=71, cli=82,
              tipo=154, obs=168)
    COL_HDR = [
        ("hi",    "H.Ini"),
        ("hf",    "H.Fin"),
        ("llave", "Llave"),
        ("pers",  "P."),
        ("dur",   "Dur.h"),
        ("dsp",   "Dsp.h"),
        ("cli",   "Cliente / Dirección / Descripción"),
        ("tipo",  "Tipo / Frec."),
        ("obs",   "Observaciones"),
    ]
    ROW_H = 17*mm

    for dia in DIAS:
        servicios = servicios_por_dia.get(dia, [])

        # Day header
        c.setFillColor(TEAL)
        c.rect(12*mm, y - 7*mm, W - 24*mm, 7*mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 9)
        fecha_dia = servicios[0].get("fecha", "") if servicios else ""
        h_dia = sum(float(s.get("duracion_h",0)) + float(s.get("desplazamiento_h",0))
                    for s in servicios)
        dia_label = f"{dia}   {fecha_dia}" if fecha_dia else dia
        c.drawString(14*mm, y - 4.5*mm, dia_label)
        c.drawRightString(W - 14*mm, y - 4.5*mm, f"{h_dia:.1f} h estimadas")
        y -= 7*mm

        if not servicios:
            c.setFillColor(GRAY_LIGHT)
            c.rect(12*mm, y - 7*mm, W - 24*mm, 7*mm, fill=1, stroke=0)
            c.setStrokeColor(GRAY_LINE); c.setLineWidth(0.3)
            c.rect(12*mm, y - 7*mm, W - 24*mm, 7*mm, fill=0, stroke=1)
            c.setFillColor(GRAY_MID); c.setFont("Helvetica-Oblique", 7.5)
            c.drawCentredString(W/2, y - 4.5*mm, "Sin servicios asignados")
            y -= 9*mm
            continue

        # Column header
        c.setFillColor(TEAL_MED)
        c.rect(12*mm, y - 5.5*mm, W - 24*mm, 5.5*mm, fill=1, stroke=0)
        c.setStrokeColor(GRAY_LINE); c.setLineWidth(0.3)
        c.rect(12*mm, y - 5.5*mm, W - 24*mm, 5.5*mm, fill=0, stroke=1)
        c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 6)
        for key, label in COL_HDR:
            c.drawString(CX[key]*mm + 1*mm, y - 3.5*mm, label)
        y -= 5.5*mm

        # Service rows
        for idx, s in enumerate(servicios):
            two_p = int(s.get("personas", 1)) >= 2
            bg = ORANGE_L if two_p else (GRAY_LIGHT if idx % 2 == 0 else WHITE)

            c.setFillColor(bg)
            c.rect(12*mm, y - ROW_H, W - 24*mm, ROW_H, fill=1, stroke=0)
            if two_p:
                c.setFillColor(ORANGE)
                c.rect(12*mm, y - ROW_H, 1.5*mm, ROW_H, fill=1, stroke=0)
            c.setStrokeColor(GRAY_LINE); c.setLineWidth(0.3)
            c.rect(12*mm, y - ROW_H, W - 24*mm, ROW_H, fill=0, stroke=1)

            # Horas
            c.setFillColor(GRAY_DARK); c.setFont("Helvetica-Bold", 8)
            c.drawString(CX["hi"]*mm + 1*mm, y - 5*mm,
                         s.get("hora_inicio", ""))
            c.setFont("Helvetica", 7.5)
            c.drawString(CX["hf"]*mm + 1*mm, y - 5*mm,
                         s.get("hora_fin", ""))

            # Llave
            llave = str(s.get("llave", ""))
            c.setFillColor(TEAL if llave else GRAY_MID)
            c.setFont("Helvetica-Bold" if llave else "Helvetica", 7.5)
            c.drawString(CX["llave"]*mm + 1*mm, y - 5*mm, llave or "—")

            # Personas
            c.setFillColor(ORANGE if two_p else TEAL)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(CX["pers"]*mm + 1*mm, y - 5*mm,
                         str(s.get("personas", 1)))

            # Dur / Dsp
            c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 7.5)
            c.drawString(CX["dur"]*mm + 1*mm, y - 5*mm,
                         str(s.get("duracion_h", "")))
            c.drawString(CX["dsp"]*mm + 1*mm, y - 5*mm,
                         str(s.get("desplazamiento_h", "")))

            # Cliente / dirección / descripción (3 líneas)
            c.setFillColor(GRAY_DARK); c.setFont("Helvetica-Bold", 7.5)
            cli = s.get("cliente", "")
            if len(cli) > 42: cli = cli[:42] + "…"
            c.drawString(CX["cli"]*mm + 1*mm, y - 4.5*mm, cli)

            c.setFont("Helvetica", 6.5); c.setFillColor(GRAY_MID)
            addr = s.get("direccion", "")
            if len(addr) > 50: addr = addr[:50] + "…"
            c.drawString(CX["cli"]*mm + 1*mm, y - 9.5*mm, addr)

            c.setFont("Helvetica-Oblique", 6.5)
            desc = s.get("descripcion", "")
            if len(desc) > 52: desc = desc[:52] + "…"
            c.drawString(CX["cli"]*mm + 1*mm, y - 14*mm, desc)

            # Tipo + frecuencia (dos líneas)
            tipo_code = s.get("tipo", "")
            frec_code = s.get("frecuencia", "")
            c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 7)
            c.drawString(CX["tipo"]*mm + 1*mm, y - 4.5*mm, tipo_code)
            c.setFont("Helvetica", 6.5); c.setFillColor(GRAY_MID)
            frec_label = FRECUENCIA.get(frec_code, frec_code)
            c.drawString(CX["tipo"]*mm + 1*mm, y - 9.5*mm, frec_label)

            # Observaciones (2 líneas si hace falta, dentro de 30mm)
            c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 6.5)
            obs = s.get("observaciones", "")
            max_ch = 22
            if len(obs) > max_ch:
                c.drawString(CX["obs"]*mm + 1*mm, y - 4.5*mm, obs[:max_ch])
                resto = obs[max_ch:max_ch*2]
                if len(obs) > max_ch*2: resto += "…"
                c.drawString(CX["obs"]*mm + 1*mm, y - 9.5*mm, resto)
            else:
                c.drawString(CX["obs"]*mm + 1*mm, y - 5*mm, obs)

            y -= ROW_H

        # Fila de pausa
        c.setFillColor(TEAL_LIGHT)
        c.rect(12*mm, y - 5*mm, W - 24*mm, 5*mm, fill=1, stroke=0)
        c.setStrokeColor(TEAL); c.setLineWidth(0.3)
        c.rect(12*mm, y - 5*mm, W - 24*mm, 5*mm, fill=0, stroke=1)
        c.setFillColor(TEAL); c.setFont("Helvetica", 6.5)
        c.drawString(14*mm, y - 3.3*mm, "Pausa desayuno / comida")
        c.drawRightString(W - 14*mm, y - 3.3*mm,
                          "H.INICIO: ________     H.FIN: ________")
        y -= 8*mm

    # ── Nota final ───────────────────────────────────────────────
    nota_y = max(y - 2*mm, 20*mm)
    c.setFillColor(TEAL_LIGHT)
    c.rect(12*mm, nota_y - 10*mm, W - 24*mm, 10*mm, fill=1, stroke=0)
    c.setStrokeColor(TEAL); c.setLineWidth(0.6)
    c.rect(12*mm, nota_y - 10*mm, W - 24*mm, 10*mm, fill=0, stroke=1)
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 7.5)
    c.drawString(14*mm, nota_y - 4*mm, "NOTA:")
    c.setFillColor(GRAY_DARK); c.setFont("Helvetica", 7)
    c.drawString(30*mm, nota_y - 4*mm,
        "Las llaves dejadas para servicios deben devolverse en la siguiente faena cursada.")

    _footer(c)
    c.save()


# ═════════════════════════════════════════════════════════════════
# DEMO — ejecutar directamente para generar PDFs de muestra
# ═════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import os
    OUT = "/Users/enric/TAGMA/salida"
    os.makedirs(OUT, exist_ok=True)

    # -- Albarán de muestra --
    albaran_data = {
        "id_albaran":   "6197 - 000027",
        "fecha":        "16/04/2026",
        "cliente":      "3890 - Srs. C.P. Calle Ángel Guimerà, 30-34",
        "direccion":    "Carrer d'Àngel Guimerà, 30-34, 08917 Badalona, Barcelona",
        "poblacion":    "Badalona · Barcelona",
        "tipo_servicio":"AB",
        "ambito":       "Vestíbulo",
        "tareas": [
            "Abrillantado pavimento. Proteger zonas delicadas.",
            "Repasar rincones con medios mecánicos.",
            "Limpieza previa del pavimento antes del abrillantado.",
        ],
        "material": [
            "Rotativa 50 cm + Extensión cable",
            "Lana de acero · Abrillantador específico",
            "Protector (Cartón / plástico)",
        ],
        "observaciones": (
            "Plazo de seguridad de 12 horas tras la actuación. "
            "Señalizar zona húmeda con conos de seguridad antes de abandonar el inmueble."
        ),
        "ejecucion": [{
            "dia": "16/04/2026", "tecnico": "Juan Adelson",
            "hora_inicio": "08:00", "hora_fin": "09:30", "tiempo_min": "90",
        }],
        "tecnico": "Juan Adelson",
    }
    generar_albaran(albaran_data, f"{OUT}/Albaran_6197-000027_JuanAdelson.pdf")
    print("✓ Albarán generado")

    # -- Hoja de ruta de muestra --
    servicios = {
        "LUNES":     [],
        "MARTES":    [],
        "MIÉRCOLES": [
            {"fecha": "16/04/2026", "hora_inicio": "07:30", "hora_fin": "09:00",
             "llave": "", "personas": 1, "duracion_h": "1.0",
             "desplazamiento_h": "0.5", "frecuencia": "M",
             "cliente": "6580 - Srs. Facil Mobel Retail, S.L",
             "direccion": "Paseo Fabra i Puig, 103, 08016 Barcelona",
             "descripcion": "Limpieza cristales EXTERIOR-INTERIOR",
             "tipo": "LC", "observaciones": ""},
            {"fecha": "16/04/2026", "hora_inicio": "09:30", "hora_fin": "11:00",
             "llave": "", "personas": 1, "duracion_h": "1.0",
             "desplazamiento_h": "0.5", "frecuencia": "Q",
             "cliente": "6587 - Srs. Facil Mobel Retail, S.L",
             "direccion": "Calle Rosellón, 498, 08025 Barcelona",
             "descripcion": "Limpieza cristales EXTERIOR",
             "tipo": "LC", "observaciones": ""},
        ],
        "JUEVES": [
            {"fecha": "23/04/2026", "hora_inicio": "06:00", "hora_fin": "08:00",
             "llave": "", "personas": 2, "duracion_h": "2.0",
             "desplazamiento_h": "0.5", "frecuencia": "T",
             "cliente": "RESTAURANTE CANFEU",
             "direccion": "Carrer del Pintor Borrassà, 43, 08205 Sabadell",
             "descripcion": "Totalidad ventanas. Hacer con CASA SANDRA.",
             "tipo": "LC", "observaciones": "Hacer con Casa Sandra"},
            {"fecha": "23/04/2026", "hora_inicio": "09:30", "hora_fin": "12:00",
             "llave": "", "personas": 2, "duracion_h": "2.0",
             "desplazamiento_h": "0.3", "frecuencia": "A",
             "cliente": "Casa Sandra",
             "direccion": "Carrer del Forn del Raig, 48A, 08211 Castellar del Vallès",
             "descripcion": "Ventanas y balconeras. Llevar patucos.",
             "tipo": "LC", "observaciones": "Llevar patucos para los zapatos"},
            {"fecha": "23/04/2026", "hora_inicio": "13:00", "hora_fin": "13:40",
             "llave": "", "personas": 1, "duracion_h": "0.66",
             "desplazamiento_h": "0.2", "frecuencia": "M",
             "cliente": "C.P. Latorre 69 y 71",
             "direccion": "Carrer Latorre 69 y 71, 08203 Sabadell",
             "descripcion": "Limpieza puerta de entrada",
             "tipo": "LC", "observaciones": ""},
        ],
        "VIERNES": [
            {"fecha": "24/04/2026", "hora_inicio": "07:00", "hora_fin": "08:30",
             "llave": "", "personas": 1, "duracion_h": "1.5",
             "desplazamiento_h": "0.3", "frecuencia": "S",
             "cliente": "6580 - Srs. Facil Mobel Retail, S.L",
             "direccion": "Plaça de Gal·la Placídia, 24, 08006 Barcelona",
             "descripcion": "Local EXTERIOR",
             "tipo": "LC", "observaciones": ""},
        ],
    }
    generar_hoja_ruta(
        "Juan Adelson (JUANKA)",
        "14 al 18 de Abril 2026",
        17, 2026, servicios,
        f"{OUT}/HojaRuta_Semana17_JuanAdelson.pdf"
    )
    print("✓ Hoja de ruta generada")
    print(f"\nArchivos en {OUT}/")
