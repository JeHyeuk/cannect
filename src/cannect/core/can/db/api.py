from cannect.config import env
from cannect.core.can.db.read import CANDBReader
from cannect.core.can.db.dbc import to_dbc
from cannect.core.can.db.doc import Specification
from cannect.errors import CANDBDuplicationError
from pathlib import Path
from typing import Union

class DB(CANDBReader):

    def to_dbc(self, engine_type:str, channel:Union[int, str], *exclude:str):
        if isinstance(channel, int):
            if engine_type == "HEV":
                channel = {1:'P', 2:'H', 3:'L'}[channel]
            else:
                channel = {1:'P', 2:'L', 3:'L'}[channel]

        channel = channel.upper()
        if not channel in ['P', 'H', 'L']:
            raise KeyError(f'Unsupported channel: {channel}')

        if not self.rev.endswith(engine_type):
            base = self.by_engine(engine_type)
        else:
            base = self.copy()
            base = base[base[f'{engine_type} Channel'] == channel]

        if exclude:
            base = base[~base['Message'].isin(exclude)]

        duplicated = []
        for _id, df in base.groupby("ID"):
            msg = df["Message"].unique()
            if len(msg) > 1:
                duplicated.append((_id, msg))
        if duplicated:
            for _id, msg in duplicated:
                print(f'IN CHANNEL: {channel}, ID: "{_id}" IS DUPLICATED BY: "{msg.tolist()}"')
            raise CANDBDuplicationError()

        if channel == 'L' and engine_type == 'HEV':
            n_channel = '3'
        else:
            n_channel = {'P': 1, 'H': 2, 'L': '2, 3'}[channel]
        filename = f'{engine_type}-CAN{n_channel}.dbc'
        to_dbc(env.DOWNLOADS / filename, base)
        return

    def to_docx(self, engine_type:str):
        if not self.rev.endswith(engine_type):
            base = self.by_engine(engine_type)
        else:
            base = self.copy()

        docx = Specification(base)
        docx.generate(f'{"_".join(base.src.split("_")[:-1])}_{base.rev}.docx')
        return



if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)


    db = DB()
    db.to_developer_mode('HEV')
    print(db[db['Message'].str.startswith('MCU')])
    # print(db.src)
    # print(db.rev)
    # print(db)
    # print(db.is_developer_mode())
    #
    # db1 = db.by_engine('HEV')
    # print(db1.src)
    # print(db1.rev)
    # print(db1)
    # print(db1.is_developer_mode())
    #
    # db.to_developer_mode('HEV')
    # print(db.src)
    # print(db.rev)
    # print(db)
    # print(db.is_developer_mode())

    # db.to_docx("ICE")
    # db.to_dbc("HEV", 1, "CVVD1")