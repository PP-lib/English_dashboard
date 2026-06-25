#!/usr/bin/env python3
"""授業の発話内容から「累計語彙」を蓄積し、語彙の伸びを分析する。

目的: ユニーク単語数を効率的に伸ばすため、
  - これまでに使った単語（累計語彙）を記録
  - 毎回の授業で新しく使った単語（new words）を数える
  - 使い回している頻出単語を把握し、次に狙う単語選びの土台にする

出力:
  - data/vocabulary.csv : word, first_date, total_count（全授業で使った単語の一覧）
  - 画面に: 回ごとの新規単語数、累計語彙サイズ、頻出語、1回しか使っていない語など

使い方:
  python3 vocab.py
  python3 vocab.py --new 2026-06-25   # 指定日に「初めて使った単語」を一覧表示
"""
import csv
import glob
import os
import sys
from collections import Counter

import analyze

ROOT = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPT_DIR = os.path.join(ROOT, "data", "transcripts")
VOCAB_CSV = os.path.join(ROOT, "data", "vocabulary.csv")


def lessons():
    """(date, tokens) を日付昇順で返す。"""
    out = []
    for path in sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.txt"))):
        date = os.path.basename(path)[:10]
        with open(path, encoding="utf-8") as f:
            tokens = analyze.tokenize(f.read())   # フィラー除外済み
        out.append((date, tokens))
    return out


def build():
    data = lessons()
    seen = {}              # word -> first_date
    total = Counter()      # word -> 全授業での出現数
    per_lesson = []        # 各回の (date, unique, new_words[list])
    cumulative = 0
    for date, tokens in data:
        total.update(tokens)
        uniq = set(tokens)
        new = sorted(w for w in uniq if w not in seen)
        for w in new:
            seen[w] = date
        cumulative = len(seen)
        per_lesson.append({
            "date": date,
            "unique": len(uniq),
            "new": new,
            "new_count": len(new),
            "cumulative": cumulative,
        })
    return seen, total, per_lesson


def write_vocab_csv(seen, total):
    rows = sorted(seen.keys(), key=lambda w: (seen[w], -total[w], w))
    with open(VOCAB_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["word", "first_date", "total_count"])
        for word in rows:
            w.writerow([word, seen[word], total[word]])


def main(argv):
    seen, total, per_lesson = build()
    write_vocab_csv(seen, total)

    if len(argv) > 2 and argv[1] == "--new":
        day = argv[2]
        for L in per_lesson:
            if L["date"] == day:
                print(f"{day} に初めて使った単語 ({L['new_count']}語):")
                print(", ".join(L["new"]))
                return 0
        print(f"{day} のデータが見つかりません。")
        return 1

    print(f"累計語彙数（全授業のユニーク語）: {len(seen)} 語")
    print(f"語彙ファイル: {VOCAB_CSV}\n")
    print("回ごとの推移:")
    print(f"  {'日付':<12}{'その回のユニーク':>10}{'新規単語':>10}{'累計語彙':>10}")
    for L in per_lesson:
        print(f"  {L['date']:<12}{L['unique']:>10}{L['new_count']:>10}{L['cumulative']:>10}")

    once = sorted(w for w in total if total[w] == 1)
    print(f"\n1回しか使っていない単語: {len(once)} 語（伸ばし代）")
    print("頻出トップ20（使い回している語）:")
    for w, c in total.most_common(20):
        print(f"  {w:<14}{c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
