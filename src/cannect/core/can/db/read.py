from cannect.core.can.db.schema.keys import CAN_DB_KEYS
from cannect.core.can.db.vcs import CANDBVcs
from cannect.schema.candb import CanSignal, CanMessage
from cannect.schema.datadictionary import DataDictionary
from cannect.utils.deco import single_arg_constraint

from pandas import DataFrame, Series
from typing import Union
import pandas as pd


class CANDBReader(DataFrame):

    _metadata = ["official", "rev", "src"]

    @classmethod
    def typecast(cls, raw_db:DataFrame) -> DataFrame:
        if "Message" in raw_db.columns:
            db = raw_db[~raw_db["Message"].isna()]
        else:
            db = raw_db

        for col, prop in CAN_DB_KEYS.items():
            if col not in db.columns:
                continue
            if not isinstance(db[col].dtype, prop["dtype"]):
                if prop["dtype"] == float:
                    db[col] = db[col].apply(lambda v: 0 if not v else v)
                try:
                    db[col] = db[col].astype(prop["dtype"])
                except ValueError as e:
                    raise ValueError(f'Error while type casting :{col} to {prop["dtype"]}; {e}')
        return db.fillna("")

    def __init__(
        self,
        base:Union[str, DataFrame]='자체제어기_KEFICO-EMS_CANFD',
        rev:Union[int, str]='',
        **kwargs # @src, @rev 직접 입력 시 사용
    ):
        if isinstance(base, str):
            vcs = CANDBVcs(base)
            self.src = base
            self.rev = vcs.log.revision[0] if not rev else vcs.check_revision(rev)
            self.official = kwargs.get('official', True)
            data = pd.read_json(vcs if not rev else vcs[rev], orient='index')
        elif isinstance(base, DataFrame):
            self.src = kwargs.get('src', '<pandas; DataFrame>')
            self.rev = rev
            self.official = kwargs.get('official', False)
            data = base
        else:
            raise TypeError('읽을 수 없는 형식의 CAN DB 입니다.')

        super().__init__(self.typecast(data))
        return

    @property
    def _constructor(self):
        return CANDBReader

    @property
    def _constructor_sliced(self):
        return Series # 또는 커스텀 Series 클래스

    @property
    def messages(self) -> DataDictionary[str, CanMessage]:
        return DataDictionary({msg:CanMessage(df) for msg, df in self.groupby(by="Message")})

    @property
    def signals(self) -> DataDictionary:
        return DataDictionary({str(sig["Signal"]):CanSignal(sig) for _, sig in self.iterrows()})

    @single_arg_constraint("ICE", "HEV")
    def by_engine(self, engine_type:str):
        if self.rev.endswith(f'@{engine_type}'):
            pass
        elif '@' in self.rev:
            self.rev = self.rev.split('@')[0] + f'@{engine_type}'
        else:
            self.rev += f'@{engine_type}'
        return self[self[f'{engine_type} Channel'] != ""]

    def is_developer_mode(self):
        return "Channel" in self.columns

    def to_developer_mode(self, engine_type:str):

        def _msg2chn(msg:str, chn:str) -> str:
            """
            Channel P,H 메시지 구분
            :param msg:
            :param chn:
            :return:
            """
            if not msg.endswith("ms"):
                return f"{msg}_{chn}"
            empty = []
            for part in msg.split("_"):
                if part.endswith("ms"):
                    empty.append(chn)
                empty.append(part)
            return "_".join(empty)

        channel = f'{engine_type} Channel'
        base = self.by_engine(engine_type)
        base["Channel"] = base[channel]
        base["WakeUp"] = base[f"{engine_type} WakeUp"]
        base["Signal"] = base[["Signal", "SignalRenamed"]] \
                        .apply(lambda x: x.SignalRenamed if x.SignalRenamed else x.Signal, axis=1)

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
        super().__init__(base)
        self.rev += '-DEV'
        return


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    db = CANDBReader()
    print(db.src)
    print(db.rev)
    print(db)
    print(db.is_developer_mode())

    db1 = db.by_engine('HEV')
    print(db1.src)
    print(db1.rev)
    print(db1)
    print(db1.is_developer_mode())

    db.to_developer_mode('HEV')
    print(db.src)
    print(db.rev)
    print(db)
    print(db.is_developer_mode())

    # db = CANDBReader(rev=21580)
    # print(db.src)
    # print(db.rev)
    # print(db)

