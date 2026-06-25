#!/usr/bin/env python3
"""オンライン英会話の文字起こしから成績指標を算出するモジュール。

算出する指標:
  - total_utterances : 総発話数（文字起こしの発話セグメント数）
  - total_words      : 総単語数（フィラー除外後）
  - unique_words     : ユニーク単語数（フィラー除外後）
  - wpm              : Words Per Minute（total_words / 授業時間[分]）
  - ttr              : 語彙多様性 Type-Token Ratio（unique_words / total_words）

単体実行:
  python3 analyze.py data/transcripts/2026-06-25_life-in-indonesia-and-japan.txt
"""
import re
import sys
from collections import Counter

# 1授業の標準時間（分）。WPMの分母。日ごとに揃えて比較できるよう固定値を既定とする。
DEFAULT_LESSON_MINUTES = 25.0

# 非語彙的なフィラー（言いよどみ）。単語数・WPMから除外する。
FILLERS = {
    "ah", "ahh", "uh", "uhh", "um", "umm", "hmm", "hmmm", "hm",
    "mm", "mmm", "mhm", "eh", "er", "err", "oh", "huh",
}

# 単語トークンの正規表現（don't, i'd などのアポストロフィを許容）
_WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")


def segments(text):
    """発話セグメント（空行で区切られた非空行）のリストを返す。"""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def tokenize(text, exclude_fillers=True):
    """テキストを小文字の単語トークン列に分割する。"""
    tokens = _WORD_RE.findall(text.lower())
    if exclude_fillers:
        tokens = [t for t in tokens if t not in FILLERS]
    return tokens


def analyze(text, lesson_minutes=DEFAULT_LESSON_MINUTES, exclude_fillers=True):
    """文字起こしテキストを受け取り、指標の辞書を返す。"""
    segs = segments(text)
    tokens = tokenize(text, exclude_fillers=exclude_fillers)
    total_words = len(tokens)
    unique_words = len(set(tokens))

    # 参考: 除外したフィラーの内訳
    all_tokens = tokenize(text, exclude_fillers=False)
    filler_breakdown = {
        w: c for w, c in Counter(all_tokens).items() if w in FILLERS
    }

    return {
        "total_utterances": len(segs),
        "total_words": total_words,
        "unique_words": unique_words,
        "wpm": round(total_words / lesson_minutes, 1) if lesson_minutes else None,
        "ttr": round(unique_words / total_words, 3) if total_words else None,
        "lesson_minutes": lesson_minutes,
        "filler_count": sum(filler_breakdown.values()),
        "filler_breakdown": filler_breakdown,
    }


def _main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    with open(argv[1], encoding="utf-8") as f:
        text = f.read()
    minutes = float(argv[2]) if len(argv) > 2 else DEFAULT_LESSON_MINUTES
    r = analyze(text, lesson_minutes=minutes)
    print(f"ファイル          : {argv[1]}")
    print(f"授業時間(分)      : {r['lesson_minutes']}")
    print(f"総発話数          : {r['total_utterances']}")
    print(f"総単語数(除フィラー): {r['total_words']}")
    print(f"ユニーク単語数    : {r['unique_words']}")
    print(f"WPM               : {r['wpm']}")
    print(f"TTR(語彙多様性)   : {r['ttr']}")
    print(f"除外フィラー計    : {r['filler_count']}  {r['filler_breakdown']}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
