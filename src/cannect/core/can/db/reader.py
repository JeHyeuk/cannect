from cannect.core.can.db.schema import SCHEMA
from cannect.core.can.db.vcs import CANDBVcs
from cannect.schema.candb import CanSignal, CanMessage
from cannect.schema.datadictionary import DataDictionary


from pandas import DataFrame
from typing import Dict, Union
import pandas as pd
import os


class CANDBReader:
    """
    CAN DB 데이터프레임
    데이터프레임 R/W 및 메시지, 신호 단위 접근
    """
    def __init__(self, src:Union[str, DataFrame]='', **kwargs):
        if isinstance(src, DataFrame):
            source = kwargs["source"] if "source" in kwargs else 'direct'
            traceability = kwargs["traceability"] if "traceability" in kwargs else 'Untraceable'
            __db__ = src.copy()
        else:
            if not str(src):
                src = CANDBVcs().json
            source = src
            traceability = "_".join(os.path.basename(source).split("_")[:-1])
            __db__ = pd.read_json(source, orient='index')

        __db__ = __db__[~__db__["Message"].isna()]
        for col, prop in SCHEMA.items():
            if col not in __db__.columns:
                continue
            if not isinstance(__db__[col].dtype, prop["dtype"]):
                if prop["dtype"] == float:
                    __db__[col] = __db__[col].apply(lambda v: 0 if not v else v)
                try:
                    __db__[col] = __db__[col].astype(prop["dtype"])
                except ValueError as e:
                    raise ValueError(f'Error while type casting :{col} to {prop["dtype"]}; {e}')
        __db__.fillna("", inplace=True)

        self.db = __db__
        self.source = source
        self.traceability = traceability
        self.revision = traceability.split("_V")[0].split("_")[-1]
        return

    def __str__(self) -> str:
        return str(self.db)

    def __repr__(self):
        return repr(self.db)

    def __getitem__(self, item):
        __get__ = self.db.__getitem__(item)
        if isinstance(__get__, DataFrame):
            return CANDBReader(__get__, source=self.source, traceability=self.traceability)
        return __get__

    def __len__(self) -> int:
        return len(self.db)

    def __setitem__(self, key, value):
        self.db.__setitem__(key, value)

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.db.__getattr__(item)

    @property
    def messages(self) -> DataDictionary:
        return DataDictionary({msg:CanMessage(df) for msg, df in self.db.groupby(by="Message")})

    @property
    def signals(self) -> Union[Dict[str, CanSignal], DataDictionary]:
        return DataDictionary({str(sig["Signal"]):CanSignal(sig) for _, sig in self.db.iterrows()})

    def mode(self, engine_spec:str):
        return CANDBReader(self[self[f'{engine_spec} Channel'] != ""].copy(), source=self.source, traceability=self.traceability)

    def is_developer_mode(self):
        return "Channel" in self.db.columns

    def to_developer_mode(self, engine_spec:str):
        """
        :param engine_spec: ["ICE", "HEV"]
        :return:
        """
        channel = f'{engine_spec} Channel'
        base = self[self[channel] != ""].copy()

        # Channel P,H 메시지 구분
        def _msg2chn(msg:str, chn:str) -> str:
            if not msg.endswith("ms"):
                return f"{msg}_{chn}"
            empty = []
            for part in msg.split("_"):
                if part.endswith("ms"):
                    empty.append(chn)
                empty.append(part)
            return "_".join(empty)

        base["Channel"] = base[channel]
        base["WakeUp"] = base[f"{engine_spec} WakeUp"]
        base["Signal"] = base[["Signal", "SignalRenamed"]].apply(
            lambda x: x["SignalRenamed"] if x["SignalRenamed"] else x["Signal"],
            axis=1
        )

        multi_channel_message = base[base[channel].str.contains(',')]['Message'].unique()
        objs = [base]
        for msg in multi_channel_message:
            signals = base[base["Message"] == msg]
            channels = []
            for chn in signals[channel].unique():
                if len(chn) >= len(channels):
                    channels = chn.split(",")
            for chn in channels:
                unique = signals[signals[channel].str.contains(chn)].copy()
                unique["Message"] = unique["Message"].apply(lambda x: _msg2chn(x, chn))
                unique["Signal"] = unique["Signal"] + f"_{chn}"
                unique["SignalRenamed"] = unique["SignalRenamed"].apply(lambda x: x + f"_{chn}" if x else "")
                unique["Channel"] = chn
                objs.append(unique)

        base = pd.concat(objs=objs, axis=0, ignore_index=True)
        base = base[~base["Message"].isin(multi_channel_message)]
        return CANDBReader(base, source=self.source, traceability=self.traceability)


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    db = CANDBReader()
    # print(db)
    print(db.source)
    print(db.traceability)
    print(db.revision)
    # print(db.to_developer_mode("ICE").revision)
    # print(db.messages['ABS_ESC_01_10ms'])
    # print(db.columns)
    # print(db.is_developer_mode())
    # db2 = db.to_developer_mode("HEV")
    # print(db2[db2["Message"].str.contains("MCU")])