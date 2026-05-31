from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


OUT_DIR = Path(__file__).resolve().parent
PDF_PATH = OUT_DIR / "hakuryu_ai_visitor_poster.pdf"


FONT = "HeiseiKakuGo-W5"
FONT_MINCHO = "HeiseiMin-W3"


def draw_round_rect(c, x, y, w, h, fill, stroke="#D8DEE9", radius=16, width=1):
    c.saveState()
    c.setStrokeColor(colors.HexColor(stroke))
    c.setFillColor(colors.HexColor(fill))
    c.setLineWidth(width)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    c.restoreState()


def draw_centered(c, text, x, y, w, size, color="#0F2742", font=FONT):
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(colors.HexColor(color))
    c.drawCentredString(x + w / 2, y, text)
    c.restoreState()


def draw_text(c, text, x, y, size=12, color="#26384D", font=FONT):
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(colors.HexColor(color))
    c.drawString(x, y, text)
    c.restoreState()


def draw_lines(c, lines, x, y, size=12, leading=18, color="#26384D", font=FONT):
    for line in lines:
        draw_text(c, line, x, y, size=size, color=color, font=font)
        y -= leading
    return y


def main():
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_MINCHO))

    c = canvas.Canvas(str(PDF_PATH), pagesize=A4)
    page_w, page_h = A4
    margin = 42
    content_w = page_w - margin * 2

    # Background
    c.setFillColor(colors.HexColor("#FDFDFD"))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Header
    header_h = 142
    draw_round_rect(c, margin, page_h - margin - header_h, content_w, header_h, "#E8ECF5", "#E8ECF5", radius=24, width=0)
    draw_centered(c, "白龍AIガイド", margin, page_h - margin - 58, content_w, 38, "#0F2742")
    draw_centered(c, "企画・場所・待ち時間をすばやく確認できます", margin, page_h - margin - 91, content_w, 15, "#2B5C8A")
    draw_centered(c, "画面の案内に沿って操作してください", margin, page_h - margin - 118, content_w, 11, "#44546A")

    # Feature cards
    card_y = page_h - margin - header_h - 28 - 92
    gap = 12
    card_w = (content_w - gap * 2) / 3
    features = [
        ("企画を探す", ["企画名・内容", "場所を確認"]),
        ("待ち時間を見る", ["空いている企画を", "チェック"]),
        ("予定を確認", ["ステージや", "当日の案内"]),
    ]
    for i, (title, body_lines) in enumerate(features):
        x = margin + i * (card_w + gap)
        draw_round_rect(c, x, card_y, card_w, 92, "#FFFFFF", "#D7DCE8", radius=14)
        draw_centered(c, title, x, card_y + 58, card_w, 15, "#0F2742")
        y = card_y + 35
        for line in body_lines:
            draw_centered(c, line, x, y, card_w, 10.5, "#334155")
            y -= 15

    # Example questions
    box_y = card_y - 128
    draw_round_rect(c, margin, box_y, content_w, 104, "#F8FAFC", "#D7DCE8", radius=16)
    draw_text(c, "おすすめの聞き方", margin + 20, box_y + 74, size=15, color="#0F2742")
    questions = [
        "「オカダナルドはどこ？」",
        "「飲食企画を教えて」",
        "「待ち時間が短い企画は？」",
        "「今日の外ステージ予定を教えて」",
    ]
    draw_lines(c, questions[:2], margin + 24, box_y + 49, size=11.5, leading=18, color="#26384D")
    draw_lines(c, questions[2:], margin + content_w / 2 + 10, box_y + 49, size=11.5, leading=18, color="#26384D")

    # Important note
    note_y = box_y - 106
    draw_round_rect(c, margin, note_y, content_w, 82, "#FFF8E8", "#ECD9A6", radius=16)
    draw_text(c, "大切なお願い", margin + 20, note_y + 55, size=15, color="#5C4200")
    note_lines = [
        "AIの回答は、パンフレットや登録済み資料をもとにした案内です。",
        "最新の変更、売り切れ、雨天時変更、緊急時はスタッフ・先生の案内を優先してください。",
    ]
    draw_lines(c, note_lines, margin + 24, note_y + 34, size=10.5, leading=17, color="#4A3A13")

    # QR and wait-time area
    bottom_y = margin + 86
    qr_w = 148
    draw_round_rect(c, margin, bottom_y, qr_w, 150, "#FFFFFF", "#9AA6B8", radius=10, width=1.4)
    draw_centered(c, "QRコード", margin, bottom_y + 88, qr_w, 19, "#0F2742")
    draw_centered(c, "ここに貼付", margin, bottom_y + 62, qr_w, 11, "#667085")
    draw_centered(c, "スマホで待ち時間", margin, bottom_y + 38, qr_w, 10, "#667085")

    right_x = margin + qr_w + 16
    right_w = content_w - qr_w - 16
    draw_round_rect(c, right_x, bottom_y, right_w, 150, "#F5F7FB", "#D7DCE8", radius=16)
    draw_text(c, "スマホで待ち時間を見る場合", right_x + 20, bottom_y + 112, size=15, color="#0F2742")
    wait_lines = [
        "掲示されているQRコードを読み取ってください。",
        "待ち時間は目安です。実際の列の状況とずれる場合があります。",
        "困ったときは、近くの白龍祭スタッフに声をかけてください。",
    ]
    draw_lines(c, wait_lines, right_x + 22, bottom_y + 84, size=10.5, leading=19, color="#26384D")

    # Footer
    footer = "白龍AIガイドは案内を手伝うためのシステムです。最終案内は当日のスタッフ・先生の指示を優先してください。"
    draw_centered(c, footer, margin, margin + 34, content_w, 8.8, "#667085")

    c.showPage()
    c.save()
    print(PDF_PATH)


if __name__ == "__main__":
    main()
