# -*- coding: utf-8 -*-

try:
    from opencc import OpenCC
except Exception:  # pragma: no cover - optional dependency fallback
    OpenCC = None


_T2S = OpenCC("t2s") if OpenCC else None
_S2T = OpenCC("s2t") if OpenCC else None

_T2S_FALLBACK = str.maketrans({
    "蘿": "萝",
    "莉": "莉",
    "髮": "发",
    "僕": "仆",
    "絲": "丝",
    "轉": "转",
    "鐵": "铁",
    "異": "异",
    "環": "环",
    "檔": "档",
    "絕": "绝",
    "鳴": "鸣",
    "聲": "声",
    "優": "优",
    "彌": "弥",
    "聖": "圣",
    "園": "园",
    "愛": "爱",
    "長": "长",
    "離": "离",
    "萬": "万",
    "與": "与",
    "藍": "蓝",
    "艦": "舰",
    "隊": "队",
    "連": "连",
    "結": "结",
})

_S2T_FALLBACK = str.maketrans({
    "萝": "蘿",
    "发": "髮",
    "仆": "僕",
    "丝": "絲",
    "转": "轉",
    "铁": "鐵",
    "异": "異",
    "环": "環",
    "档": "檔",
    "绝": "絕",
    "鸣": "鳴",
    "声": "聲",
    "优": "優",
    "弥": "彌",
    "圣": "聖",
    "园": "園",
    "爱": "愛",
    "长": "長",
    "离": "離",
    "万": "萬",
    "与": "與",
    "蓝": "藍",
    "舰": "艦",
    "队": "隊",
    "连": "連",
    "结": "結",
})


def to_simplified(text):
    value = str(text or "")
    if _T2S:
        return _T2S.convert(value)
    return value.translate(_T2S_FALLBACK)


def to_traditional(text):
    value = str(text or "")
    if _S2T:
        return _S2T.convert(value)
    return value.translate(_S2T_FALLBACK)
