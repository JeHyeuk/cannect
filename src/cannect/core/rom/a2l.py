from pandas import DataFrame, Series
from pathlib import Path
from pya2l import DB
from typing import Union
import pandas as pd
import pya2l.model as model



class A2L:

    def __init__(self, file:Union[Path, str]):
        self.src_a2l = src = Path(file)
        if (src.parent / f'{src.name}db').exists():
            self.session = DB().open_existing(str(src.parent / f'{src.name}db'))
        else:
            self.session = DB().import_a2l(str(file))
        return

    def __loop__(self, iterable):
        keys = []
        objs = []
        for m in iterable:
            if not keys:
                keys = [key for key in m.__dict__ if not key.startswith('_')]
            obj = {}
            for key in keys:
                obj[key] = m.__dict__[key]
            objs.append(obj)
        return DataFrame(objs)

    @property
    def measurements(self) -> DataFrame:
        # return self.session.query(model.Measurement).all()
        return self.__loop__(self.session.query(model.Measurement).all())

    @property
    def characteristics(self) -> DataFrame:
        # return self.session.query(model.Characteristic).all()
        return self.__loop__(self.session.query(model.Characteristic).all())

    @property
    def axis_pts_list(self):
        return self.session.query(model.AxisPts).all()

    @property
    def elements(self) -> Series:
        return pd.concat([self.measurements, self.characteristics], ignore_index=True)['name']






if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    kef = A2L(r"C:\Users\Administrator\Downloads\generated_code_KEFICO\generated_code_KEFICO\a2l\VTC_BoostCtlr.a2l")
    gtx = A2L(r"C:\Users\Administrator\Downloads\generated_code_GTX\generated_code_GTX\a2l\VTC_BoostCtlr.a2l")
    print(set(kef.elements) - set(gtx.elements))
    print(set(gtx.elements) - set(kef.elements))


    gm = gtx.characteristics.copy()
    gm.columns = [f'{c}_gtx' for c in gm.columns]
    gm.set_index(keys='name_gtx', inplace=True)

    km = kef.characteristics.copy()
    km.columns = [f'{c}_kef' for c in km.columns]
    km.set_index(keys='name_kef', inplace=True)

    df = gm.join(km)
    for col in gtx.characteristics.columns:
        if col == 'name':
            continue
        df[col] = df[f'{col}_gtx'] == df[f'{col}_kef']
    df = df[[c for c in gtx.characteristics.columns if (c != 'name') and (not c.endswith('_id'))]]
    print(df)

    for c in df:
        filt = df[df[c] == False]
        if not filt.empty:
            print(filt)


    # print(gtx.characteristics)