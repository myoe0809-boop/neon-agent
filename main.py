
import os
import re
import html
import zipfile
from datetime import datetime, timezone
from groq import Groq

MODEL = "openai/gpt-oss-20b"

FALLBACK_CARDS = [
    ("今日も大好き！", "오늘도 정말 좋아해!"),
    ("ずっと応援してるよ", "언제나 응원하고 있어"),
    ("最高の時間をありがとう", "최고의 시간을 선물해 줘서 고마워"),
    ("また会いに来たよ", "다시 만나러 왔어"),
    ("あなたが私の宝物", "당신은 나의 보물이야"),
    ("世界で一番輝いてる！", "세상에서 가장 빛나!"),
]

def generate_content():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY secret is missing.")

    client = Groq(api_key=api_key)

    prompt = """
Create original Japanese phrases for a printable Japanese idol fan message card kit.

Return exactly this format:
TITLE|A short Korean product title
CARD|Japanese phrase|Korean translation
CARD|Japanese phrase|Korean translation
CARD|Japanese phrase|Korean translation
CARD|Japanese phrase|Korean translation
CARD|Japanese phrase|Korean translation
CARD|Japanese phrase|Korean translation
DESCRIPTION|A short Korean product description
TAGS|tag1, tag2, tag3

Rules:
- Exactly six CARD lines.
- Japanese must be natural and grammatically correct.
- Keep each Japanese phrase short enough for a small printed card.
- Make the phrases varied, warm, and suitable for idol fans.
- Do not use real idol names, logos, copyrighted characters, or song lyrics.
- Do not add explanations or Markdown.
- Never use the | character inside the content.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You create original, commercially usable digital stationery."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content or ""

def parse_content(content):
    title = "일본 아이돌 팬 메시지 카드 세트"
    description = "일본어 응원 문구가 담긴 인쇄용 팬 메시지 카드입니다."
    tags = "일본어, 아이돌, 팬굿즈"
    cards = []

    for line in content.splitlines():
        line = line.strip().strip("`")
        parts = line.split("|")

        if len(parts) < 2:
            continue

        kind = parts[0].strip().upper()

        if kind == "TITLE":
            title = parts[1].strip()
        elif kind == "CARD" and len(parts) >= 3:
            cards.append((parts[1].strip(), parts[2].strip()))
        elif kind == "DESCRIPTION":
            description = parts[1].strip()
        elif kind == "TAGS":
            tags = parts[1].strip()

    if len(cards) < 6:
        cards = FALLBACK_CARDS

    return title, description, tags, cards[:6]

def make_html(title, cards):
    card_html = ""

    for japanese, korean in cards:
        card_html += f"""
        <div class="card">
          <div class="small">MY FAVORITE PERSON</div>
          <div class="name">推しの名前</div>
          <div class="japanese">{html.escape(japanese)}</div>
          <div class="korean">{html.escape(korean)}</div>
          <div class="decoration">♡ ✦ ♡</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
@page {{ size: A4 portrait; margin: 10mm; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: Arial, "Noto Sans KR", sans-serif;
  color: #403344;
  background: #fff;
}}
.sheet {{
  width: 190mm;
  height: 277mm;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: repeat(3, 1fr);
  gap: 6mm;
}}
.card {{
  border: 1.5px solid #d9a9c9;
  border-radius: 5mm;
  background: #fff8fc;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 5mm;
  overflow: hidden;
}}
.small {{
  font-size: 8pt;
  letter-spacing: 2px;
  color: #b17c9d;
}}
.name {{
  margin-top: 5mm;
  font-size: 12pt;
  color: #b17c9d;
}}
.japanese {{
  margin-top: 7mm;
  font-family: "Noto Sans JP", sans-serif;
  font-size: 20pt;
  font-weight: bold;
  line-height: 1.5;
}}
.korean {{
  margin-top: 3mm;
  font-size: 10pt;
  color: #806a7c;
}}
.decoration {{
  margin-top: 7mm;
  color: #ce8bb2;
  font-size: 18pt;
}}
@media screen {{
  body {{ padding: 15px; }}
  .sheet {{ margin: auto; }}
}}
@media print {{
  body {{ padding: 0; }}
}}
</style>
</head>
<body>
<div class="sheet">
{card_html}
</div>
</body>
</html>"""

def main():
    print("NEON: 상품 콘텐츠 제작 시작")

    content = generate_content()
    title, description, tags, cards = parse_content(content)

    os.makedirs("reports", exist_ok=True)

    html_content = make_html(title, cards)
    html_path = "reports/fan_message_cards.html"
    zip_path = "reports/fan_message_printable_kit.zip"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    readme = f"""상품명: {title}

상품 설명:
{description}

검색 태그:
{tags}

사용 방법:
1. fan_message_cards.html 파일을 브라우저에서 엽니다.
2. 인쇄 기능을 선택합니다.
3. A4 용지, 배율 100%로 인쇄하거나 PDF로 저장합니다.
4. 카드의 점선 또는 테두리를 따라 잘라 사용합니다.

주의:
이 파일은 상품 초안입니다.
일본어 문구, 디자인, 인쇄 결과와 판매 권리를 확인한 뒤 판매하십시오.
"""

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("fan_message_cards.html", html_content)
        z.writestr("README.txt", readme)

    report = f"""# NEON 상품 제작 보고서

상품명: {title}

설명: {description}

태그: {tags}

## 제작된 파일
- fan_message_cards.html
- fan_message_printable_kit.zip

## 검토 필요
- 일본어 문구의 자연스러움
- 인쇄 시 글자와 여백
- 상품 디자인의 독창성
- 판매 플랫폼의 수수료 및 등록 조건

실제 판매 및 수익은 아직 발생하지 않았습니다.
"""

    with open("reports/product_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print("상품 ZIP 생성 완료:", zip_path)

if __name__ == "__main__":
    main()

