from pathlib import Path
from typing import Dict, TypeVar
import pprint, os

KT = TypeVar("KT")
VT = TypeVar("VT")

class DataDictionary(Dict[KT, VT]):
    """
    데이터 저장 Dictionary
    built-in: dict의 확장으로 저장 요소에 대해 attribute 접근 방식을 허용
    기본 제공 Alias (별칭): dD, dDict
    """
    def __init__(self, data=None, **kwargs):
        super().__init__()

        data = data or {}
        data.update(kwargs)
        for key, value in data.items():
            if isinstance(value, dict):
                self[key] = DataDictionary(**value)
                continue
            # list나 다른 타입들은 변환 없이 그대로 저장
            self[key] = value
        return

    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        return super().__getattribute__(attr)

    def __setattr__(self, attr, value):
        if isinstance(value, dict):
            self[attr] = DataDictionary(**value)
        else:
            self[attr] = value
        return

    def __str__(self) -> str:
        return pprint.pformat(self)

# 별칭 설정
dD = dDict = DataDictionary
