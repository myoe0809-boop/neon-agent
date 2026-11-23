
import os
import html
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from groq import Groq

MODEL = "openai/gpt-oss-20b"

FALLBACK_CARDS = [
    ("いつも応援してるよ！", "항상 응원하고 있어요!"),
    ("あなたの笑顔が大好き！", "당신의 미소가 정말 좋아요!"),
    ("ずっと輝いていてね", "언제나 빛나 주세요"),
    ("会えて本当にうれしい！", "만나서 정말 기뻐요!"),
    ("心からありがとう", "진심으로 고마워요"),
    ("これからも大好き！", "앞으로도 정말 좋아할게요!"),
]

COLORS = [
    ("#FFF0F5", "#D98BB5"),
    ("#F0F5FF", "#8BA9D9"),
    ("#F4F0FF", "#A68BD9"),
    ("#FFF8E8", "#D9B56E"),
    ("#EDFAF5", "#83BFA6"),
    ("#FFF0EE", "#D99183"),
]

def generate_cards():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY secret is missing.")

    client = Groq(api_key=key)

    prompt = """
Create exactly six natural Japanese messages for idol fans.
Return exactly six lines in this format:
CARD|Japanese phrase|Accurate Korean translation

Rules:
- Natural Japanese used by real fans.
- Warm, affectionate, short messages.
- Each phrase should fit on a small printable card.
- Korean translations must be accurate and natural.
- No real idol names, lyrics, logos, or copyrighted characters.
- No explanations or Markdown.
- Never use | inside a phrase.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You create original Japanese fan stationery."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6
    )

    cards = []
    for line in (response.choices[0].message.content or "").splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 3 and parts[0].strip().upper() == "CARD":
            cards.append((parts[1].strip(), parts[2].strip()))

    if len(cards) != 6:
        return FALLBACK_CARDS

    return cards

def make_html(cards):
    blocks = ""

    for i, (jp, kr) in enumerate(cards):
        bg, accent = COLORS[i]
        blocks += f"""
        <div class="card" style="background:{bg}; border-color:{accent}">
          <div class="top" style="color:{accent}">MY FAVORITE PERSON</div>
          <div class="name">推しの名前</div>
          <div class="jp">{html.escape(jp)}</div>
          <div class="kr">{html.escape(kr)}</div>
          <div class="stars" style="color:{accent}">♡ ✦ ♡</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>일본 아이돌 팬 메시지 카드</title>
<style>
@page {{ size: A4 portrait; margin: 10mm; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family:Arial,"Noto Sans KR",sans-serif; color:#493d4b; }}
.sheet {{
 width:190mm; height:277mm; display:grid;
 grid-template-columns:1fr 1fr;
 grid-template-rows:repeat(3,1fr); gap:6mm;
}}
.card {{
 border:1.5px solid; border-radius:5mm;
 display:flex; flex-direction:column; align-items:center;
 justify-content:center; text-align:center; padding:5mm;
 overflow:hidden;
}}
.top {{ font-size:8pt; letter-spacing:2px; }}
.name {{ margin-top:5mm; font-size:12pt; color:#98758f; }}
.jp {{ margin-top:7mm; font-family:"Noto Sans JP",sans-serif;
 font-size:19pt; font-weight:bold; line-height:1.5; }}
.kr {{ margin-top:4mm; font-size:10pt; color:#806a7c; }}
.stars {{ margin-top:7mm; font-size:18pt; }}
@media screen {{ body {{ padding:15px; }} .sheet {{ margin:auto; }} }}
@media print {{ body {{ padding:0; }} }}
</style>
</head>
<body><div class="sheet">{blocks}</div></body>
</html>"""

def make_pdf(cards, path):
    page_w, page_h = A4
    c = canvas.Canvas(path, pagesize=A4)

    margin = 28
    gap = 17
    card_w = (page_w - 2 * margin - gap) / 2
    card_h = (page_h - 2 * margin - 2 * gap) / 3

    for i, (jp, kr) in enumerate(cards):
        col = i % 2
        row = i // 2

        x = margin + col * (card_w + gap)
        y = page_h - margin - (row + 1) * card_h - row * gap

        bg, accent = COLORS[i]
        c.setFillColor(HexColor(bg))
        c.setStrokeColor(HexColor(accent))
        c.roundRect(x, y, card_w, card_h, 14, fill=1, stroke=1)

        c.setFillColor(HexColor(accent))
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + card_w / 2, y + card_h - 30, "MY FAVORITE PERSON")

        c.setFillColor(HexColor("#98758F"))
        c.setFont("Helvetica", 11)
        c.drawCentredString(x + card_w / 2, y + card_h - 58, "Oshi name")

        c.setFillColor(HexColor("#493D4B"))
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(x + card_w / 2, y + card_h / 2 + 8, f"Message {i+1}")

        c.setFillColor(HexColor("#806A7C"))
        c.setFont("Helvetica", 9)
        c.drawCentredString(x + card_w / 2, y + card_h / 2 - 14, "See HTML file for Japanese text")

        c.setFillColor(HexColor(accent))
        c.setFont("Helvetica", 16)
        c.drawCentredString(x + card_w / 2, y + 25, "♡  *  ♡")

    c.save()

def main():
    print("NEON: 팬 메시지 카드 제작 시작")

    cards = generate_cards()
    os.makedirs("reports", exist_ok=True)

    html_content = make_html(cards)

    html_path = "reports/fan_message_cards.html"
    pdf_path = "reports/fan_message_cards.pdf"
    zip_path = "reports/fan_message_printable_kit.zip"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    make_pdf(cards, pdf_path)

    readme = """일본 아이돌 팬 메시지 카드 키트

구성:
- fan_message_cards.html
- fan_message_cards.pdf

HTML 파일에는 일본어 원문과 한국어 번역이 포함되어 있습니다.
PDF 파일은 인쇄용 미리보기입니다.

상업적 판매 전 일본어 문구와 PDF의 글꼴 및 인쇄 품질을 확인하십시오.
"""

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(html_path, "fan_message_cards.html")
        z.write(pdf_path, "fan_message_cards.pdf")
        z.writestr("README.txt", readme)

    with open("reports/product_report.md", "w", encoding="utf-8") as f:
        f.write("# NEON 상품 제작 보고서\n\n")
        f.write("일본 아이돌 팬 메시지 카드 6종을 생성했습니다.\n")
        f.write("- HTML 카드\n- PDF 파일\n- ZIP 상품 패키지\n\n")
        f.write("실제 판매 및 수익은 아직 발생하지 않았습니다.\n")

    print("상품 파일 생성 완료")
    print("HTML:", html_path)
    print("PDF:", pdf_path)
    print("ZIP:", zip_path)

if __name__ == "__main__":
    main()
