import argparse
import time
from pathlib import Path

import librosa
import numpy as np
import sounddevice as sd  # type:ignore
import soundfile as sf  # type:ignore

from x68pcm.okicodec import OkiCodec


def generate_dither_noise(length, amplitude=1.0):
    """
    1.0 LSB 程度の微小なノイズを生成
    """
    rng = np.random.default_rng()
    # 振幅を非常に小さく設定
    return rng.uniform(-amplitude, amplitude, length)


sr_list = [3900, 5200, 7800, 10400, 15600]


def encode(args: argparse.Namespace):
    # 1. 音声データの読み込み
    data, fs_orig = librosa.load(args.input, sr=None)  # sr=Noneでオリジナルレート維持

    # 2. リサンプリング
    sr = sr_list[args.sr]
    data_resampled = librosa.resample(data, orig_sr=fs_orig, target_sr=sr)

    # 3. ディザリング
    if args.dither:
        data_resampled += generate_dither_noise(
            len(data_resampled), 16 / 32768)

    # 4. int16へ変換
    data_resampled = np.clip(data_resampled * 2047,
                             -2048, 2047).astype(np.int16)

    # 5. ADPCMエンコード
    codec = OkiCodec()
    buf = bytearray()
    count = 0
    for sample in data_resampled:
        code = codec.encode_sample(sample)
        if count & 1:
            buf[-1] |= code << 4
        else:
            buf.append(code)
        count += 1

    if args.output:
        pcm = Path(args.output)
    else:
        pcm = Path(args.input).with_suffix(".pcm")
    with pcm.open("wb") as f:
        f.write(buf)


def decode(args: argparse.Namespace):
    sr = sr_list[args.sr]
    pcm = Path(args.input)

    codec = OkiCodec()
    samples = []
    for b in pcm.read_bytes():
        code1 = codec.decode_sample(b & 15)
        code2 = codec.decode_sample(b >> 4)
        samples.append(code1)
        samples.append(code2)
    data = np.array(samples, dtype=np.int16)

    # 12bit -> 16bit
    data *= 1 << (16 - 12)

    if args.output:
        wav = Path(args.output)
        if wav.suffix.lower() != ".wav":
            raise ValueError(f"{args.output}: wav file only")

        sf.write(args.output, data, samplerate=sr)
    else:
        sd.play(data, samplerate=sr)
        duration = len(data) / sr
        time.sleep(duration)


def main():
    parser = argparse.ArgumentParser(description="x68k ADPCM converter")
    parser.add_argument("mode", choices="de", action="store",
                        help="specify mode. d=decode/play or e=encode")
    parser.add_argument("input", help="specify input file")

    parser.add_argument(
        "-o", dest="output", action="store", type=str, help="specify output file")
    parser.add_argument("-s", dest="sr", action="store", type=int, default=4,
                        metavar="N", choices=[0, 1, 2, 3, 4],
                        help="sample rate (0=3.9, 1=5.2, 3=7.8, 3=10.4, 4=15.6) KHz default=4")
    parser.add_argument(
        "-d", "--dither", help="enable dithering", action='store_true')
    args = parser.parse_args()

    try:
        if args.mode == "e":
            encode(args)
        elif args.mode == "d":
            decode(args)
    except Exception as e:
        print(f"{type(e).__name__}({e})")
        exit(1)


if __name__ == "__main__":
    main()
