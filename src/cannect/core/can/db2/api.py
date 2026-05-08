from cannect.config import env
from cannect.core.can.db2.read import CANDBReader
from cannect.core.can.db2.dbc import to_dbc
from cannect.core.can.db2.doc import Specification
from cannect.errors import CANDBDuplicationError
from typing import Union

class DB(CANDBReader):

    def to_dbc(self, engine_type:str, channel:Union[int, str], **kwargs):
        if not self.rev.endswith(engine_type):
            base = self.by_engine(engine_type)
        else:
            base = self.copy()

        if isinstance(channel, int):
            if engine_type == "HEV":
                channel = {1:'P', 2:'H', 3:'L'}[channel]
            else:
                channel = {1:'P', 2:'L', 3:'L'}[channel]

        channel = channel.upper()
        if not channel in ['P', 'H', 'L']:
            raise KeyError(f'Unsupported channel: {channel}')

        base = base[base[f'{engine_type} Channel'] == channel]

        if 'Codeword' in kwargs:
            cfg = ''.join([c for c in kwargs['Codeword'][:-2] if not c in ['=', '<', '>', ' ']])
            mask1 = base['Codeword'].str.replace(" ", "") == kwargs['Codeword'].replace(" ", "")
            mask2 = (base['Codeword'] == '') | (~base['Codeword'].str.contains(cfg))
            base = base[mask1 | mask2]
        if 'SystemConstant' in kwargs:
            base = base[
                (base['SystemConstant'].str.replace(" ", "") == kwargs['SystemConstant'].replace(" ", "")) |
                (base['SystemConstant'] == '')
            ]
        for _id, df in base.groupby("ID"):
            msg = df["Message"].unique()
            if len(msg) > 1:
                raise CANDBDuplicationError(f'IN CHANNEL: {channel}, ID: "{_id}" IS DUPLICATED BY "{msg.tolist()}", SPECIFY {{Codeword}} or {{SystemConstant}}')

        if channel == 'L' and engine_type == 'HEV':
            n_channel = '3'
        else:
            n_channel = {'P': 1, 'H': 2, 'L': '2, 3'}[channel]
        filename = f'{engine_type}-CAN{n_channel}'
        if kwargs:
            filename += "-" + "-".join([f'{{{val}}}' for val in kwargs.values()])
        filename += '.dbc'
        to_dbc(env.DOWNLOADS / filename, base)
        return

    def to_docx(self, engine_type:str):
        if not self.rev.endswith(engine_type):
            base = self.by_engine(engine_type)
        else:
            base = self.copy()

        docx = Specification(base)
        docx.generate(env.DOWNLOADS / f'{"_".join(base.src.name.split("_")[:-1])}_{db.rev}.docx')
        return



if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)
    from cannect import mount
    mount(r"E:\\SVN")

    db = DB()
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

    db.to_docx("ICE")