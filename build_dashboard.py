#!/usr/bin/env python3
"""data/transcripts/ 配下の全文字起こしを集計し、結果CSVとダッシュボードHTMLを生成する。

使い方:
  1. data/transcripts/ に「YYYY-MM-DD_タイトル.txt」の形式で文字起こしを置く
  2. python3 build_dashboard.py を実行
  3. data/results.csv と dashboard.html が更新される（dashboard.html をブラウザで開く）

WPMの分母（生徒の発話時間）:
  data/audio/ に同名の音声があれば audio_speaking_time.py で自動推定し、
  data/lessons.csv にキャッシュする。手動修正は lessons.csv の speaking_minutes を編集。
  音声が無い日は授業長（analyze.DEFAULT_LESSON_MINUTES = 25分）で代用する。
"""
import csv
import glob
import os
import json
import re

import analyze

ROOT = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPT_DIR = os.path.join(ROOT, "data", "transcripts")
AUDIO_DIR = os.path.join(ROOT, "data", "audio")
RESULTS_CSV = os.path.join(ROOT, "data", "results.csv")
LESSONS_META = os.path.join(ROOT, "data", "lessons.csv")
DASHBOARD_HTML = os.path.join(ROOT, "index.html")  # GitHub Pages公開用

LESSON_LENGTH_MIN = analyze.DEFAULT_LESSON_MINUTES  # 1授業の長さ（参考WPM用）

_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[_-](.*)$")


def _load_lessons_meta():
    """data/lessons.csv を date -> {speaking_minutes, source} で読み込む。"""
    meta = {}
    if os.path.exists(LESSONS_META):
        with open(LESSONS_META, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                d = (row.get("date") or "").strip()
                if not d:
                    continue
                sm = row.get("speaking_minutes", "").strip()
                meta[d] = {
                    "speaking_minutes": float(sm) if sm else None,
                    "source": (row.get("source") or "").strip(),
                }
    return meta


def _save_lessons_meta(meta):
    with open(LESSONS_META, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "speaking_minutes", "source"])
        for d in sorted(meta):
            m = meta[d]
            sm = "" if m["speaking_minutes"] is None else f"{m['speaking_minutes']:.2f}"
            w.writerow([d, sm, m.get("source", "")])


def _find_audio(date, title_stem):
    for ext in (".mp3", ".m4a", ".wav"):
        for cand in (f"{date}_{title_stem}{ext}", f"{date}{ext}"):
            p = os.path.join(AUDIO_DIR, cand)
            if os.path.exists(p):
                return p
        # 日付プレフィックスに一致する任意の音声
        for p in glob.glob(os.path.join(AUDIO_DIR, f"{date}*{ext}")):
            return p
    return None


def _student_speaking_minutes(date, title_stem, meta):
    """生徒の発話時間(分)を取得。優先順: lessons.csvの値 > 音声から推定 > None。

    音声から推定した場合は lessons.csv にキャッシュ（再計算を避ける）。
    手動修正したい場合は lessons.csv の speaking_minutes を編集すればよい。
    """
    if date in meta and meta[date]["speaking_minutes"] is not None:
        return meta[date]["speaking_minutes"]
    audio = _find_audio(date, title_stem)
    if not audio:
        return None
    print(f"  音声から発話時間を推定中: {os.path.basename(audio)} ...")
    import audio_speaking_time as ast
    r = ast.diarize(audio)
    sm = round(r["student_min"], 2)
    meta[date] = {"speaking_minutes": sm, "source": "auto"}
    return sm


def _parse_name(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    m = _NAME_RE.match(stem)
    if not m:
        return None, stem, stem.replace("-", " ")
    date, title_stem = m.group(1), m.group(2)
    return date, title_stem, title_stem.replace("-", " ").replace("_", " ").strip()


def collect():
    meta = _load_lessons_meta()
    rows = []
    for path in sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt"))):
        date, title_stem, title = _parse_name(path)
        with open(path, encoding="utf-8") as f:
            text = f.read()

        speaking_min = _student_speaking_minutes(date, title_stem, meta)
        # WPMの分母: 発話時間が分かればそれ、無ければ授業長
        denom = speaking_min if speaking_min else LESSON_LENGTH_MIN
        r = analyze.analyze(text, lesson_minutes=denom)
        wpm_lesson = round(r["total_words"] / LESSON_LENGTH_MIN, 1)

        rows.append({
            "date": date or "",
            "title": title,
            "total_utterances": r["total_utterances"],
            "total_words": r["total_words"],
            "unique_words": r["unique_words"],
            "speaking_minutes": speaking_min if speaking_min else "",
            "wpm": r["wpm"],                 # 生徒の発話時間あたり（主指標）
            "wpm_lesson": wpm_lesson,        # 授業時間あたり（参考）
            "ttr": r["ttr"],
            "filler_count": r["filler_count"],
        })
    rows.sort(key=lambda x: x["date"])
    _save_lessons_meta(meta)
    return rows


def write_csv(rows):
    fields = ["date", "title", "total_utterances", "total_words",
              "unique_words", "speaking_minutes", "wpm", "wpm_lesson",
              "ttr", "filler_count"]
    with open(RESULTS_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_html(rows):
    from datetime import datetime
    data_json = json.dumps(rows, ensure_ascii=False)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    table_rows = "\n".join(
        f"<tr><td>{r['date']}</td><td class='title'>{r['title']}</td>"
        f"<td>{r['total_utterances']}</td><td>{r['total_words']}</td>"
        f"<td>{r['unique_words']}</td>"
        f"<td>{r['speaking_minutes'] or '-'}</td>"
        f"<td><b>{r['wpm']}</b></td><td>{r['wpm_lesson']}</td>"
        f"<td>{r['ttr']}</td></tr>"
        for r in rows
    )
    html = (_TEMPLATE.replace("__DATA__", data_json)
            .replace("__TABLE__", table_rows)
            .replace("__GENERATED__", generated))
    with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
        f.write(html)


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>オンライン英会話 成績ダッシュボード</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body { font-family: -apple-system, "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
         margin: 0; padding: 24px; background:#f5f6f8; color:#1d2330; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .sub { color:#6b7280; font-size:13px; margin-bottom:20px; }
  .cards { display:flex; gap:14px; flex-wrap:wrap; margin-bottom:24px; }
  .card { background:#fff; border-radius:12px; padding:16px 20px; min-width:150px;
          box-shadow:0 1px 3px rgba(0,0,0,.08); }
  .card .label { font-size:12px; color:#6b7280; }
  .card .value { font-size:28px; font-weight:700; margin-top:4px; }
  .card .delta { font-size:12px; margin-top:2px; }
  .up { color:#16a34a; } .down { color:#dc2626; } .flat{ color:#9ca3af; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
  .panel { background:#fff; border-radius:12px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.08); }
  .panel h2 { font-size:14px; margin:0 0 10px; color:#374151; }
  table { width:100%; border-collapse:collapse; background:#fff; border-radius:12px; overflow:hidden;
          box-shadow:0 1px 3px rgba(0,0,0,.08); margin-top:18px; font-size:13px; }
  th,td { padding:9px 12px; text-align:right; border-bottom:1px solid #eef0f3; }
  th:first-child, td:first-child, td.title { text-align:left; }
  th { background:#fafbfc; color:#6b7280; font-weight:600; }
  td.title { color:#374151; }
  details.spec { background:#fff; border-radius:12px; padding:14px 18px; margin-top:18px;
                 box-shadow:0 1px 3px rgba(0,0,0,.08); font-size:13px; color:#374151; }
  details.spec summary { cursor:pointer; font-weight:600; color:#1d2330; }
  details.spec ul { margin:10px 0 4px; padding-left:18px; line-height:1.7; }
  details.spec code { background:#f1f3f5; padding:1px 5px; border-radius:4px; font-size:12px; }
  .note { color:#6b7280; font-size:12px; margin-top:6px; }
  .foot { color:#9ca3af; font-size:11px; margin-top:14px; }
  @media (max-width:760px){ .grid{ grid-template-columns:1fr; } }
</style>
</head>
<body>
  <h1>オンライン英会話 成績ダッシュボード</h1>
  <div class="sub">フィラー（ah / uh / um など言いよどみ）除外。WPM = 総単語数 ÷ <b>生徒の発話時間(分)</b>（音声から推定）。</div>

  <div class="cards" id="cards"></div>

  <div class="grid">
    <div class="panel"><h2>WPM の推移（発話時間あたり）</h2><canvas id="wpm"></canvas></div>
    <div class="panel"><h2>ユニーク単語数の推移</h2><canvas id="uniq"></canvas></div>
    <div class="panel"><h2>総単語数の推移</h2><canvas id="words"></canvas></div>
    <div class="panel"><h2>生徒の発話時間(分)の推移</h2><canvas id="spk"></canvas></div>
  </div>

  <table>
    <thead><tr><th>日付</th><th>レッスン</th><th>総発話数</th><th>総単語数</th>
    <th>ユニーク単語</th><th>発話時間(分)</th><th>WPM<br>(発話時間)</th>
    <th>WPM<br>(授業25分)</th><th>TTR</th></tr></thead>
    <tbody>__TABLE__</tbody>
  </table>

  <details class="spec">
    <summary>計算条件（クリックで展開）</summary>
    <ul>
      <li><b>総発話数</b>: 文字起こしの発話セグメント数（空行で区切られた非空行を1発話）。</li>
      <li><b>総単語数</b>: 英単語トークン数（小文字化、<code>[a-z]+('[a-z]+)?</code>）。
          <b>フィラー除外</b> = <code>ah, uh, um, hmm, hm, mm, eh, er, oh, huh</code> など。
          <code>yeah / yes / right / so / like</code> 等の意味語は残す。</li>
      <li><b>ユニーク単語数</b>: フィラー除外後の異なり語数（レンマ化なし）。</li>
      <li><b>発話時間</b>: 音声（あなたの声のみの録音）をVADで解析し、発話部分の合計時間。
          無音・先生のターンは除外。</li>
      <li><b>WPM（発話時間）</b> = 総単語数 ÷ 発話時間(分)　／　<b>WPM（授業25分）</b> = 総単語数 ÷ 25。</li>
      <li><b>TTR</b> = ユニーク単語数 ÷ 総単語数（語彙多様性）。</li>
    </ul>
    <div class="note">詳細な定義は <code>CALCULATION.md</code> を参照。</div>
  </details>
  <div class="foot">生成日時: __GENERATED__</div>

<script>
const DATA = __DATA__;
const labels = DATA.map(d => d.date);

function card(label, value, prev){
  let delta = '';
  if (prev !== undefined && prev !== null && value !== null){
    const diff = (value - prev).toFixed(value % 1 ? 1 : 0);
    const cls = diff > 0 ? 'up' : (diff < 0 ? 'down' : 'flat');
    const arrow = diff > 0 ? '▲' : (diff < 0 ? '▼' : '–');
    delta = `<div class="delta ${cls}">${arrow} ${Math.abs(diff)} 前回比</div>`;
  }
  return `<div class="card"><div class="label">${label}</div>
          <div class="value">${value ?? '-'}</div>${delta}</div>`;
}

const last = DATA[DATA.length-1] || {};
const prev = DATA[DATA.length-2] || {};
document.getElementById('cards').innerHTML =
  card('最新WPM', last.wpm, prev.wpm) +
  card('ユニーク単語', last.unique_words, prev.unique_words) +
  card('総単語数', last.total_words, prev.total_words) +
  card('総発話数', last.total_utterances, prev.total_utterances) +
  card('レッスン数', DATA.length);

function line(id, key, color){
  new Chart(document.getElementById(id), {
    type:'line',
    data:{ labels, datasets:[{ data: DATA.map(d=>d[key]),
      borderColor:color, backgroundColor:color+'22', fill:true, tension:.3,
      pointRadius:4, pointBackgroundColor:color }]},
    options:{ plugins:{legend:{display:false}}, scales:{ y:{ beginAtZero:false }}}
  });
}
line('wpm','wpm','#2563eb');
line('uniq','unique_words','#16a34a');
line('words','total_words','#d97706');
line('spk','speaking_minutes','#7c3aed');
</script>
</body>
</html>
"""


def main():
    rows = collect()
    if not rows:
        print("data/transcripts/ に文字起こし(.txt)が見つかりません。")
        return 1
    write_csv(rows)
    write_html(rows)
    print(f"集計 {len(rows)} 件 -> {RESULTS_CSV}")
    print(f"ダッシュボード -> {DASHBOARD_HTML}")
    for r in rows:
        sm = r['speaking_minutes'] or '?'
        print(f"  {r['date']}  発話{r['total_utterances']:>3}  "
              f"語{r['total_words']:>4}  ユニーク{r['unique_words']:>4}  "
              f"発話{sm}分  WPM {r['wpm']} (授業基準 {r['wpm_lesson']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
