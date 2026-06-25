# 次回授業 スピーキング・スクリプト

目的: **まだ使ったことのない単語**を意識して話し、1授業あたりのユニーク単語数を伸ばす。
あなたの累計語彙（`data/vocabulary.csv`）に入っていない語を中心に選んでいます。
話題はいつものトピック（インドネシア勤務・通勤・天気・四国・家族・移民・登山）。

使い方:
1. 下の「言い換え」で口ぐせ（so / very / good / maybe …）を別の語に置き換える練習をする
2. トピック別フレーズを声に出す
3. 最後の「そのまま話せるモノローグ」を授業の自己紹介・近況報告で使う

---

## 1. 口ぐせを言い換える（最優先）

あなたは `so`(208回) `very`(76) `good`(32) `maybe`(35) を多用しています。
同じ意味を別の語で言うだけでユニーク数が一気に増えます。

| よく使う語 | 言い換え（新規語） | 例 |
|---|---|---|
| very | extremely / incredibly / remarkably | It's **extremely** humid today. |
| very good | excellent / superb / outstanding | The food was **excellent**. |
| so (だから) | therefore / that's why / as a result | **Therefore**, I left early. |
| maybe | perhaps / possibly / presumably | **Perhaps** it will rain. |
| a lot of | numerous / plenty of / a great deal of | There are **numerous** motorbikes. |
| big | massive / enormous / huge | An **enormous** traffic jam. |
| hard (大変) | demanding / exhausting / tough | A **demanding** commute. |
| I think | I suppose / I reckon / it seems to me | **I reckon** it's faster by train. |

---

## 2. トピック別 新規語彙＋例文

### 通勤・交通（commute & traffic）
- **commute（通勤）** / **congestion（渋滞）** / **gridlock（大渋滞）**: My daily **commute** can turn into total **gridlock** when it rains.
- **bumper to bumper（数珠つなぎ）**: The cars were **bumper to bumper** for two hours.
- **detour（迂回）** / **pothole（道路の穴）**: I had to take a **detour** around the **potholes**.
- **outskirts（郊外）** / **rural（田舎の）** / **remote（辺ぴな）**: My factory sits on the **outskirts**, in a **remote**, **rural** area.

### 天気・気候（weather & climate）
- **humid（蒸し暑い）** / **sweltering（うだるように暑い）** / **scorching（焼けつく）**: It was **sweltering**, almost **scorching**.
- **power outage / blackout（停電）**: A four-hour **blackout** shut down every air conditioner.
- **temperate（温暖な）** / **mild（穏やかな）**: Shikoku has a **temperate**, **mild** climate.
- **drought（干ばつ）** / **humidity（湿度）**: The **humidity** is brutal before a **drought** breaks.

### 四国・日本（Japan & Shikoku）
- **prefecture（県）** *(既出)* → **region / province / countryside** で言い換え
- **scenic（景色のよい）** / **picturesque（絵のように美しい）**: Shikoku is **scenic** and **picturesque**.
- **agriculture（農業）** / **harvest（収穫）** / **crops（作物）**: The long sunshine is ideal for **agriculture** and a rich **harvest**.
- **dialect（方言）** / **accent（なまり）**: Each region has its own **dialect**.

### 火山・地震（natural events）
- **dormant（休火山の）** / **eruption（噴火）** / **evacuate（避難する）**: A **dormant** volcano can **erupt** and force people to **evacuate**.
- **diverted（迂回された）** / **layover（乗り継ぎ）**: My flight was **diverted**, so I had a **layover** in Singapore.

### 家族・社会（family & society）
- **newborn（新生児）** / **toddler（よちよち歩きの子）**: With a **newborn**, you wake up every two hours.
- **aging population（高齢化）** / **workforce（労働力）** / **immigrant（移民）**: An **aging population** means the **workforce** relies on **immigrants**.
- **courteous（礼儀正しい）** / **diligent（勤勉な）** / **hospitable（もてなしの心がある）**: The staff were **courteous** and **diligent**.

### 登山・趣味（the outdoors）
- **solitude（孤独・静けさ）** / **secluded（人里離れた）** / **serene（静かで穏やかな）**: I crave the **solitude** of a **secluded**, **serene** trail.
- **endurance（持久力）** / **trail running（トレラン）** / **summit（山頂）**: **Trail running** builds **endurance**; I love reaching the **summit** at dawn.

---

## 3. そのまま話せるモノローグ（近況報告用）

> For the past two weeks I couldn't attend my lessons because my Japanese boss was
> transferred back to Japan, and there were **numerous** farewell parties. Now I really
> need to **buckle down** and study again.
>
> Life here can be **demanding**. My **commute** to the factory on the **outskirts** often
> becomes **gridlock**, and lately the weather has been **sweltering**. Yesterday a
> four-hour **blackout** knocked out every air conditioner, which was almost unbearable.
>
> Still, I miss Shikoku. It has a **temperate**, **mild** climate and **picturesque**
> scenery, ideal for **agriculture**. What I crave most is **solitude** — a **secluded**,
> **serene** mountain trail at dawn, where **trail running** rebuilds my **endurance**.

---

## メンテナンス

- 新規語彙を選び直すときは `python3 vocab.py` で既存語彙を更新 → このファイルを差し替える。
- 授業後は新しい文字起こしを `data/transcripts/` に追加 → `python3 vocab.py` で「その回の新規単語数」を確認できる。
