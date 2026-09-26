"""游戏适配器注册表。"""
from .maa import MaaAdapter
from .maaend import MaaEndAdapter
from .bettergi import BetterGiAdapter
from .march7th import March7thAdapter
from .zzz import ZzzAdapter

# 名称 -> 适配器类
ADAPTERS = {
    "maa": MaaAdapter,
    "maaend": MaaEndAdapter,
    "bettergi": BetterGiAdapter,
    "march7th": March7thAdapter,
    "zzz": ZzzAdapter,
}


def create(adapter_name):
    cls = ADAPTERS.get(adapter_name)
    if cls is None:
        raise ValueError("未知适配器: {} (可选: {})".format(
            adapter_name, ", ".join(ADAPTERS.keys())))
    return cls()
