#!/usr/bin/env python3
"""音声ファイルから「生徒（あなた）がしゃべっている時間」を推定する。

前提: この録音は生徒（あなた）の声だけが入っている（先生の声は未録音）。
      よって音声中の発話部分はすべてあなたの発話とみなす（single_speaker=True）。

処理の流れ:
  1. mp3を16kHzモノラルにデコード（miniaudio, ffmpeg不要）
  2. エネルギーベースのVADで発話フレーム/無音フレームを判定
  3. 発話フレームの合計 = あなたの発話時間（無音・先生のターンは除外される）

※ 万一2人の声が入った録音を扱う場合は single_speaker=False で
  MFCCによる2話者クラスタリングに切り替えられる（発話の長い方を生徒と推定）。

出力: 生徒の推定発話時間（分）。build_dashboard.py がWPMの分母に使う。

使い方:
  python3 audio_speaking_time.py data/audio/2026-06-25_xxx.mp3
"""
import sys

import numpy as np
import miniaudio
from scipy.fftpack import dct
from sklearn.mixture import GaussianMixture

SR = 16000
FRAME = int(0.025 * SR)   # 25ms 窓
HOP = int(0.010 * SR)     # 10ms ホップ


def load_mono16k(path):
    dec = miniaudio.decode_file(
        path, output_format=miniaudio.SampleFormat.FLOAT32,
        nchannels=1, sample_rate=SR)
    x = np.frombuffer(memoryview(dec.samples), dtype=np.float32).astype(np.float64)
    return x


def frame_signal(x):
    n = 1 + max(0, (len(x) - FRAME) // HOP)
    idx = np.arange(FRAME)[None, :] + HOP * np.arange(n)[:, None]
    return x[idx] * np.hamming(FRAME)


def energy_vad(frames):
    """フレームごとの対数エネルギーから発話/無音を適応しきい値で判定。"""
    e = np.log(np.sum(frames ** 2, axis=1) + 1e-10)
    floor = np.percentile(e, 15)    # 無音側のエネルギー
    peak = np.percentile(e, 95)     # 発話側のエネルギー
    thr = floor + 0.30 * (peak - floor)
    speech = e > thr
    speech = smooth_bool(speech, min_run=20, fill_gap=15)  # 200ms/150ms
    return speech


def smooth_bool(mask, min_run=20, fill_gap=15):
    m = mask.copy()
    # 短い無音(<fill_gap)を埋める
    m = _close_gaps(m, fill_gap)
    # 短い発話(<min_run)を除去
    m = ~_close_gaps(~m, min_run)
    return m


def _close_gaps(mask, max_gap):
    m = mask.copy()
    i = 0
    n = len(m)
    while i < n:
        if not m[i]:
            j = i
            while j < n and not m[j]:
                j += 1
            if i > 0 and j < n and (j - i) <= max_gap:
                m[i:j] = True
            i = j
        else:
            i += 1
    return m


def mfcc(frames, nfilt=26, nceps=13):
    mag = np.abs(np.fft.rfft(frames, n=512, axis=1))
    pow_spec = (mag ** 2) / 512
    fb = mel_filterbank(nfilt, 512, SR)
    feat = np.dot(pow_spec, fb.T)
    feat = np.where(feat == 0, np.finfo(float).eps, feat)
    feat = np.log(feat)
    c = dct(feat, type=2, axis=1, norm="ortho")[:, :nceps]
    return c


def mel_filterbank(nfilt, nfft, sr):
    def hz2mel(f):
        return 2595 * np.log10(1 + f / 700.0)

    def mel2hz(m):
        return 700 * (10 ** (m / 2595.0) - 1)

    low, high = hz2mel(0), hz2mel(sr / 2)
    pts = mel2hz(np.linspace(low, high, nfilt + 2))
    bins = np.floor((nfft + 1) * pts / sr).astype(int)
    fb = np.zeros((nfilt, nfft // 2 + 1))
    for i in range(1, nfilt + 1):
        l, c, r = bins[i - 1], bins[i], bins[i + 1]
        for k in range(l, c):
            if c > l:
                fb[i - 1, k] = (k - l) / (c - l)
        for k in range(c, r):
            if r > c:
                fb[i - 1, k] = (r - k) / (r - c)
    return fb


def diarize(path, single_speaker=True, student=None):
    x = load_mono16k(path)
    total_sec = len(x) / SR
    frames = frame_signal(x)
    speech = energy_vad(frames)
    speech_idx = np.where(speech)[0]
    hop_sec = HOP / SR
    speech_sec = len(speech_idx) * hop_sec

    # 単一話者録音（あなたの声だけ）: 発話部分=すべてあなた
    if single_speaker or len(speech_idx) < 50:
        return dict(total_min=total_sec / 60, speech_min=speech_sec / 60,
                    student_min=speech_sec / 60, spk_min=[speech_sec / 60],
                    student_idx=0, mode="single")

    feats = mfcc(frames[speech_idx])
    # 平均減算（チャネル正規化）＋標準化
    feats = feats - feats.mean(axis=0)
    feats = (feats - feats.mean(0)) / (feats.std(0) + 1e-8)

    gm = GaussianMixture(n_components=2, covariance_type="diag",
                         n_init=3, random_state=0)
    labels = gm.fit_predict(feats)

    # 連続する発話区間ごとに多数決でラベルを平滑化
    labels = smooth_segments(speech, speech_idx, labels)

    dur = [np.sum(labels == k) * hop_sec for k in (0, 1)]
    if student is None:
        student_idx = int(np.argmax(dur))   # 発話の多い方を生徒と推定
    else:
        student_idx = student
    return dict(
        total_min=total_sec / 60,
        speech_min=speech_sec / 60,
        student_min=dur[student_idx] / 60,
        spk_min=[d / 60 for d in dur],
        student_idx=student_idx,
        mode="two",
    )


def smooth_segments(speech, speech_idx, labels):
    out = labels.copy()
    pos = {f: i for i, f in enumerate(speech_idx)}
    i = 0
    n = len(speech)
    while i < n:
        if speech[i]:
            j = i
            while j < n and speech[j]:
                j += 1
            seg = [pos[f] for f in range(i, j) if f in pos]
            if seg:
                maj = np.bincount(labels[seg]).argmax()
                out[seg] = maj
            i = j
        else:
            i += 1
    return out


def _main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    # 既定は単一話者（あなたの声だけの録音）。"two" 指定で2話者分離。
    single = not (len(argv) > 2 and argv[2] == "two")
    r = diarize(argv[1], single_speaker=single)
    print(f"ファイル        : {argv[1]}")
    print(f"音声全体        : {r['total_min']:.2f} 分")
    print(f"発話/無音       : 発話 {r['speech_min']:.2f} 分 / "
          f"無音 {r['total_min']-r['speech_min']:.2f} 分")
    if r.get("mode") == "two":
        for k, m in enumerate(r["spk_min"]):
            tag = " ← 生徒(推定)" if k == r["student_idx"] else ""
            print(f"  話者{k}        : {m:.2f} 分{tag}")
    print(f"生徒の発話時間  : {r['student_min']:.2f} 分"
          + ("  (録音はあなたの声のみ → 発話全体)" if r.get("mode") == "single" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
