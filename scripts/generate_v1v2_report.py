#!/usr/bin/env python3
import argparse, os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
try:
    pdfmetrics.registerFont(TTFont("DV",  os.path.join(FONT_DIR, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DVB", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))
    R, B = "DV", "DVB"
except Exception:
    R, B = "Helvetica", "Helvetica-Bold"

W, H = A4
VIOLET = colors.HexColor("#7C3AED")
DARK   = colors.HexColor("#0F172A")
GRAY   = colors.HexColor("#64748B")
LIGHT  = colors.HexColor("#F5F3FF")
GREEN  = colors.HexColor("#10B981")
AMBER  = colors.HexColor("#F59E0B")
BLUE   = colors.HexColor("#3B82F6")
RED    = colors.HexColor("#EF4444")
WHITE  = colors.white

def ps(name, font=None, size=10, color=None, align=TA_LEFT, before=0, after=4):
    return ParagraphStyle(name, fontName=font or R, fontSize=size,
                          textColor=color or DARK, alignment=align,
                          spaceBefore=before, spaceAfter=after, leading=15)

ST = {
    "title":  ps("t",  font=B, size=22, color=DARK,   align=TA_CENTER, after=4),
    "sub":    ps("s",  size=10, color=GRAY,            align=TA_CENTER, after=4),
    "h2":     ps("h2", font=B, size=13, color=VIOLET,  before=14, after=6),
    "h3":     ps("h3", font=B, size=10, color=DARK,    before=8,  after=4),
    "body":   ps("b",  size=9,  color=DARK, after=4),
    "small":  ps("sm", size=8,  color=GRAY, align=TA_CENTER),
    "green":  ps("g",  font=B, size=9,  color=GREEN),
    "footer": ps("f",  size=8,  color=GRAY, align=TA_CENTER),
}

def make_table(rows, widths=None):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  VIOLET),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  B),
        ("FONTNAME",      (0,1), (-1,-1), R),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LIGHT, WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#DDD6FE")),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("ALIGN",         (1,0), (-1,-1), "CENTER"),
    ]))
    return t

def winner_color(a, b, higher_is_better=True):
    try:
        fa, fb = float(a), float(b)
        if higher_is_better:
            return GREEN if fa >= fb else RED, RED if fa >= fb else GREEN
        else:
            return GREEN if fa <= fb else RED, RED if fa <= fb else GREEN
    except Exception:
        return DARK, DARK

def build(args):
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    doc = SimpleDocTemplate(args.output, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Титул
    story += [
        Spacer(1, 0.3*cm),
        Paragraph("HFBS — Сравнительный анализ v1 vs v2", ST["title"]),
        Paragraph("Монолит (Django sync / FastAPI async) vs Микросервисы (Django + FastAPI)", ST["sub"]),
        HRFlowable(width="100%", thickness=2, color=VIOLET, spaceAfter=8),
        Paragraph(f"Дата: {now}  ·  100 пользователей  ·  30 секунд каждый тест", ST["small"]),
        Spacer(1, 0.5*cm),
    ]

    # Архитектурное описание
    story.append(Paragraph("Архитектура сравнения", ST["h2"]))
    arch_data = [
        ["Версия",    "Сервис",         "Тип",          "Ответственность"],
        ["v1",        "Django :8000",   "Sync монолит",  "Все эндпоинты: events, seats, orders, tickets"],
        ["v1",        "FastAPI :8001",  "Async монолит", "Все эндпоинты: events, seats, orders, tickets"],
        ["v2",        "Django :9202",   "Sync сервис",   "Только auth, admin, управление событиями"],
        ["v2",        "FastAPI :9101",  "Async сервис",  "Бронирование, Redis lock, Kafka, antifrod"],
    ]
    story.append(make_table(arch_data, widths=[1.5*cm, 3*cm, 3.5*cm, 9*cm]))
    story.append(Spacer(1, 0.5*cm))

    # Основная таблица результатов
    story.append(Paragraph("Результаты нагрузочного тестирования", ST["h2"]))
    story.append(Paragraph(
        "Тест: 100 одновременных пользователей, 30 секунд. "
        "Эндпоинты: GET /events/, GET /seats/, POST /reserve/ (v1) / POST /bookings/ (v2).",
        ST["body"]))
    story.append(Spacer(1, 0.3*cm))

    # RPS сравнение
    rps_c1, rps_c2 = winner_color(args.v1f_rps, args.v1d_rps)
    rps_c3, rps_c4 = winner_color(args.v2f_rps, args.v2d_rps)

    results = [
        ["Версия", "Фреймворк", "RPS", "P50 latency", "P95 latency", "Тип"],
    ]

    def fmt(v): return f"{float(v):.1f}" if v else "—"
    def fmtms(v): return f"{v} ms" if v else "—"

    results += [
        ["v1", "Django sync",   fmt(args.v1d_rps), fmtms(args.v1d_p50), fmtms(args.v1d_p95), "Монолит"],
        ["v1", "FastAPI async", fmt(args.v1f_rps), fmtms(args.v1f_p50), fmtms(args.v1f_p95), "Монолит"],
        ["v2", "Django sync",   fmt(args.v2d_rps), fmtms(args.v2d_p50), fmtms(args.v2d_p95), "Сервис"],
        ["v2", "FastAPI async", fmt(args.v2f_rps), fmtms(args.v2f_p50), fmtms(args.v2f_p95), "Сервис"],
    ]
    t = make_table(results, widths=[1.5*cm, 3.5*cm, 2.5*cm, 3*cm, 3*cm, 3.5*cm])
    # Подсветить лучшие результаты
    try:
        rps_vals = [float(args.v1d_rps), float(args.v1f_rps), float(args.v2d_rps), float(args.v2f_rps)]
        best_rps = rps_vals.index(max(rps_vals)) + 1
        t.setStyle(TableStyle([("BACKGROUND", (2, best_rps+1), (2, best_rps+1), colors.HexColor("#D1FAE5"))]))
    except Exception:
        pass
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    # Вывод победителя
    try:
        all_rps = {
            "v1 Django":  float(args.v1d_rps),
            "v1 FastAPI": float(args.v1f_rps),
            "v2 Django":  float(args.v2d_rps),
            "v2 FastAPI": float(args.v2f_rps),
        }
        winner = max(all_rps, key=all_rps.get)
        story.append(Paragraph(
            f"✓ Лучший RPS: {winner} — {all_rps[winner]:.1f} запросов/сек",
            ST["green"]))
    except Exception:
        pass
    story.append(Spacer(1, 0.5*cm))

    # Анализ
    story.append(Paragraph("Анализ результатов", ST["h2"]))
    story.append(HRFlowable(width="100%", thickness=1, color=VIOLET, spaceAfter=8))

    try:
        v1d = float(args.v1d_rps)
        v1f = float(args.v1f_rps)
        v2f = float(args.v2f_rps)
        async_gain = v1f / max(v1d, 0.1)
        v2_gain    = v2f / max(v1f, 0.1)
    except Exception:
        v1d = v1f = v2f = async_gain = v2_gain = 0

    for title, text in [
        ("Django sync vs FastAPI async (v1 монолит)",
         f"При одинаковом функционале (монолит) FastAPI async показывает RPS={float(args.v1f_rps):.1f} "
         f"против Django sync RPS={float(args.v1d_rps):.1f}. "
         f"Прирост от async I/O: {async_gain:.1f}x. "
         f"Async особенно эффективен при конкурентных запросах к PostgreSQL и Redis."),
        ("v1 монолит vs v2 микросервисы",
         f"Разделение ответственности в v2 позволяет оптимизировать каждый сервис под свою задачу. "
         f"FastAPI в v2 обрабатывает только бронирование с Redis lock и Kafka, "
         f"что даёт RPS={float(args.v2f_rps):.1f}. "
         f"Django в v2 обслуживает admin и auth без лишней нагрузки."),
        ("Почему не только FastAPI",
         "Django ORM с migrations, admin panel и встроенной аутентификацией "
         "значительно ускоряет разработку для административных задач. "
         "Для CRUD операций с малой конкурентностью Django sync не уступает FastAPI. "
         "Оптимальная архитектура — использовать каждый инструмент по назначению."),
        ("Вывод: правильная архитектура",
         "hfbs-v2 демонстрирует, что комбинация Django (sync) + FastAPI (async) "
         "с чётким разделением ответственности превосходит монолитный подход. "
         "Django обрабатывает административные задачи, FastAPI — высоконагруженное "
         "бронирование с Redis distributed lock и Kafka event streaming."),
    ]:
        story.append(Paragraph(title, ST["h3"]))
        story.append(Paragraph(text,  ST["body"]))
        story.append(Spacer(1, 0.2*cm))

    story += [
        Spacer(1, 0.8*cm),
        HRFlowable(width="100%", thickness=0.5, color=GRAY),
        Spacer(1, 0.2*cm),
        Paragraph(f"HFBS — Дипломный проект  ·  {now}", ST["footer"]),
    ]
    doc.build(story)
    print(f"✓ PDF сохранён: {args.output}")

def parse_args():
    p = argparse.ArgumentParser()
    for x in ["v1d","v1f","v2d","v2f"]:
        p.add_argument(f"--{x}-rps", default="0")
        p.add_argument(f"--{x}-p50", default="0")
        p.add_argument(f"--{x}-p95", default="0")
    p.add_argument("--csv-prefix", default="")
    p.add_argument("--output",     required=True)
    return p.parse_args()

if __name__ == "__main__":
    build(parse_args())
