class OkiCodec:
    """OKI ADPCM (MSM5205等) コーデックのPython実装"""

    # ステップテーブル (49要素)
    STEP_TABLE = [
        16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73,
        80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279,
        307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963,
        1060, 1166, 1282, 1411, 1552
    ]

    # インデックス調整テーブル (16要素、4ビット入力に対応)
    INDEX_ADJUST = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]

    def __init__(self):
        self.last_sample = 0  # 前回の12bit PCM値 (-2048 ～ 2047)
        self.step_index = 0   # 現在のステップインデックス (0 ～ 48)

    def decode_sample(self, code):
        """4ビットのADPCM値を12ビットのPCM値にデコードする"""
        step = self.STEP_TABLE[self.step_index]

        # 差分(diff)の計算
        diff = step >> 3
        if code & 0x04:
            diff += step
        if code & 0x02:
            diff += step >> 1
        if code & 0x01:
            diff += step >> 2

        # 正負の反映
        if code & 0x08:
            self.last_sample -= diff
        else:
            self.last_sample += diff

        # 12ビット範囲へのクランプ (-2048 to 2047)
        if self.last_sample > 2047:
            self.last_sample = 2047
        elif self.last_sample < -2048:
            self.last_sample = -2048

        # インデックスの更新
        self.step_index += self.INDEX_ADJUST[code & 0x0F]
        if self.step_index < 0:
            self.step_index = 0
        elif self.step_index > 48:
            self.step_index = 48

        return self.last_sample

    def encode_sample(self, sample):
        """16ビットまたは12ビットのPCM値を4ビットのADPCM値にエンコードする"""
        # 入力を12ビットにスケールダウン (もし16ビット入力なら 4bit シフト)
        # ここでは元コードに合わせ、クランプのみ行う
        if sample > 2047:
            sample = 2047
        elif sample < -2048:
            sample = -2048

        diff = sample - self.last_sample
        code = 0x00

        if diff < 0:
            code = 0x08
            diff = -diff

        step = self.STEP_TABLE[self.step_index]

        if diff >= step:
            code |= 0x04
            diff -= step
        if diff >= (step >> 1):
            code |= 0x02
            diff -= (step >> 1)
        if diff >= (step >> 2):
            code |= 0x01

        # デコーダーを回して内部状態を同期させる
        self.decode_sample(code)

        return code


# --- 使用例 ---
# if __name__ == "__main__":
#     codec = OkiCodec()

#     # テスト用のPCMデータ (サイン波のシミュレーションなど)
#     pcm_data = [0, 100, 500, 1000, 1500, 1000, 500, 0, -500, -1000]

#     print("Encoding...")
#     adpcm_codes = []
#     for s in pcm_data:
#         c = codec.encode_sample(s)
#         adpcm_codes.append(c)
#     print(f"ADPCM codes: {adpcm_codes}")

#     # デコードテスト (状態をリセット)
#     codec.__init__()
#     print("\nDecoding...")
#     decoded_pcm = []
#     for c in adpcm_codes:
#         s = codec.decode_sample(c)
#         decoded_pcm.append(s)
#     print(f"Decoded PCM: {decoded_pcm}")
