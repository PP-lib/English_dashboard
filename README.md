# オンライン英会話 成績ダッシュボード

オンライン英会話（25分授業）の文字起こしから、日ごとの成績指標を算出して推移を可視化するツールです。

## 算出する指標

| 指標 | 内容 |
|---|---|
| 総発話数 | 文字起こしの発話セグメント数 |
| 総単語数 | 単語数（**フィラー除外**） |
| ユニーク単語数 | 異なり語数（フィラー除外） |
| WPM | Words Per Minute = 総単語数 ÷ **生徒の発話時間(分)** |
| TTR | 語彙多様性 = ユニーク単語数 ÷ 総単語数 |

**フィラー（言いよどみ）** … `ah, uh, um, hmm, hm, mm, eh, er, oh, huh` などの非語彙的なつなぎ音は単語数・WPMから除外します（一覧は `analyze.py` の `FILLERS`）。`yeah / yes / right / so / like` などの意味を持つ語は残しています。

**生徒の発話時間** … WPMの分母には授業25分ではなく「あなたが実際に話している時間」を使います。音声ファイルから次の手順で自動推定します（`audio_speaking_time.py`）:
1. mp3を16kHzにデコード（`miniaudio`、ffmpeg不要）
2. エネルギーベースVADで発話/無音を判定 → 総発話時間（無音は除外）
3. 発話部分のMFCCを2話者にクラスタリング（話者分離）し、**発話が長い方を生徒**と推定
4. 推定値は `data/lessons.csv` にキャッシュされ、ここを編集すれば手動修正できます

> 注: VADは無音（考えている間の沈黙）を除くため、WPMは「実際に声を出している時間あたりの発話速度」になります。値が高めに出るのはこのためです。話者推定がずれている場合は `data/lessons.csv` の `speaking_minutes` を直接修正してください。

## 使い方

1. 授業があった日、文字起こしと音声を次の名前で保存する（同じ名前にする）
   ```
   data/transcripts/YYYY-MM-DD_タイトル.txt
   data/audio/YYYY-MM-DD_タイトル.mp3
   例:
   data/transcripts/2026-06-25_life-in-indonesia-and-japan.txt
   data/audio/2026-06-25_life-in-indonesia-and-japan.mp3
   ```
   音声があるとWPMが「発話時間あたり」で算出されます（無い日は授業25分で代用）。

   必要なPythonパッケージ（初回のみ）:
   ```bash
   pip install numpy scipy scikit-learn miniaudio
   ```

2. 集計を実行する
   ```bash
   python3 build_dashboard.py
   ```

3. 生成物
   - `data/results.csv` … 全レッスンの指標一覧
   - `dashboard.html` … ブラウザで開くとカード＋推移グラフ＋表を表示

### 1ファイルだけ確認したいとき
```bash
python3 analyze.py data/transcripts/2026-06-25_life-in-indonesia-and-japan.txt   # 文字指標のみ
python3 audio_speaking_time.py data/audio/2026-06-25_life-in-indonesia-and-japan.mp3  # 発話時間の推定
```

### 発話時間を手動で修正したいとき
`data/lessons.csv` の `speaking_minutes` を書き換える（`source` を `manual` にしておくと自動再計算されない）：
```csv
date,speaking_minutes,source
2026-06-25,7.59,manual
```

## 現在の結果

| 日付 | 総発話数 | 総単語数 | ユニーク単語 | 発話時間 | WPM(発話時間) | WPM(授業25分) |
|---|---|---|---|---|---|---|
| 2026-06-25 | 45 | 1,296 | 325 | 7.59分 | 170.8 | 51.8 |

## ファイル構成
```
analyze.py              文字指標（発話数・単語数・ユニーク・TTR）
audio_speaking_time.py  音声から生徒の発話時間を推定（VAD＋話者分離）
build_dashboard.py      全レッスンを集計 → results.csv / dashboard.html
data/transcripts/       文字起こし(.txt)
data/audio/             音声(.mp3) ※Git管理外
data/lessons.csv        発話時間のキャッシュ（手動修正可）
data/results.csv        集計結果
dashboard.html          ダッシュボード（生成物）
```

## 補足
- 文字起こしは主に生徒側の発話を対象としています。
- 話者分離は2話者前提の自動推定です。生徒の発話が少ない回などで推定がずれた場合は `data/lessons.csv` で修正してください。
