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

**生徒の発話時間** … WPMの分母には授業25分ではなく「あなたが実際に話している時間」を使います。
このオンライン授業の録音には**あなたの声だけ**が入っている（先生の声は未録音）ため、
音声中の発話部分はすべてあなたの発話とみなせます。`audio_speaking_time.py` が次の手順で推定します:
1. mp3を16kHzにデコード（`miniaudio`、ffmpeg不要）
2. エネルギーベースVADで発話/無音を判定 → **発話部分の合計 = あなたの発話時間**
   （無音、および先生が話している間＝あなたが黙っている時間は自動的に除外される）
3. 推定値は `data/lessons.csv` にキャッシュされ、ここを編集すれば手動修正できます

> 注: VADは無音（考えている間の沈黙）も除くため、WPMは「実際に声を出している時間あたりの発話速度」になります。
> ※ 万一2人の声が入った録音を扱う場合は `audio_speaking_time.py` を `single_speaker=False` で呼ぶと2話者分離に切り替わります。

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
   - `index.html` … ブラウザで開くとカード＋推移グラフ＋表＋計算条件を表示

4. 反映（GitHub Pagesで公開している場合）
   ```bash
   git add -A && git commit -m "Add lesson YYYY-MM-DD" && git push
   ```

## ダッシュボードをWebページ（GitHub Pages）で見る

`index.html` をそのままGitHub Pagesで公開できます（初回のみ設定）:

1. GitHubのリポジトリ → **Settings** → **Pages**
2. **Build and deployment** → Source = **Deploy from a branch**
3. Branch = このブランチ（または `main`）、フォルダ = **/(root)** → Save
4. 数十秒後、`https://<ユーザー名>.github.io/English_dashboard/` で公開される

以降は、授業を貼り付けて `python3 build_dashboard.py` → `git push` するだけで
ページが自動更新されます（`index.html` がルートにあるため）。

> 音声(.mp3)はGit管理外ですが、発話時間は `data/lessons.csv` にキャッシュされ
> コミットされるので、ページのビルド・公開に音声ファイルは不要です。

### 1ファイルだけ確認したいとき
```bash
python3 analyze.py data/transcripts/2026-06-25_life-in-indonesia-and-japan.txt   # 文字指標のみ
python3 audio_speaking_time.py data/audio/2026-06-25_life-in-indonesia-and-japan.mp3  # 発話時間の推定
```

### 発話時間を手動で修正したいとき
`data/lessons.csv` の `speaking_minutes` を書き換える（`source` を `manual` にしておくと自動再計算されない）：
```csv
date,speaking_minutes,source
2026-06-25,12.62,manual
```

> 計算条件の詳細な定義は [`CALCULATION.md`](CALCULATION.md) を参照。

## 現在の結果

| 日付 | 総発話数 | 総単語数 | ユニーク単語 | 発話時間 | WPM(発話時間) | WPM(授業25分) |
|---|---|---|---|---|---|---|
| 2026-06-19 | 49 | 1,500 | 334 | 12.46分 | 120.4 | 60.0 |
| 2026-06-25 | 45 | 1,296 | 325 | 12.62分 | 102.7 | 51.8 |

## ファイル構成
```
analyze.py              文字指標（発話数・単語数・ユニーク・TTR）
audio_speaking_time.py  音声から生徒の発話時間を推定（VAD）
build_dashboard.py      全レッスンを集計 → results.csv / index.html
CALCULATION.md          計算条件の仕様書
data/transcripts/       文字起こし(.txt)
data/audio/             音声(.mp3) ※Git管理外
data/lessons.csv        発話時間のキャッシュ（手動修正可）
data/results.csv        集計結果
index.html              ダッシュボード（生成物・GitHub Pages公開用）
```

## 補足
- 録音はあなたの声のみ（先生の声は未録音）という前提です。発話時間＝音声中の発話部分の合計。
- 推定がずれていると感じたら `data/lessons.csv` の `speaking_minutes` を直接修正してください。
