from __future__ import annotations
from asammdf import MDF, Signal
from pandas import DataFrame
from typing import Optional, Union
import numpy as np
import pandas as pd
import os


class MdfFrame:
    def __init__(
        self,
        file: Optional[str] = None,
        df: Optional[DataFrame] = None,
        mdf: Optional[MDF] = None,
        src: Optional[str] = None,
    ):
        if df is not None:
            self.df = df
            self.mdf = mdf
            self.src = src
        elif file is not None:
            self.mdf = MDF(file)
            self.src = os.path.basename(file)
            self.df = self.mdf.to_dataframe()
            self.df.index.name = "time"
        else:
            raise ValueError("Either 'file' or 'df' must be provided.")

    def __getattr__(self, name):
        if hasattr(self.df, name):
            return getattr(self.df, name)
        return self.__getattribute__(name)

    def __getitem__(self, key) -> Union["MdfFrame", pd.Series]:
        result = self.df[key]
        if isinstance(result, DataFrame):
            return self._wrap(result.copy())
        return result

    def __setitem__(self, key, value):
        self.df[key] = value

    def __len__(self):
        return len(self.df)

    def __repr__(self):
        return repr(self.df)

    def __str__(self):
        return str(self.df)

    def _wrap(self, df: DataFrame) -> "MdfFrame":
        return MdfFrame(df=df, mdf=self.mdf, src=self.src)

    @property
    def mid(self) -> "MdfFrame":
        half = len(self.df) // 2
        quarter = len(self.df) // 4
        return self._wrap(self.df.iloc[half - quarter: half + quarter].copy())

    @property
    def reindex(self) -> "MdfFrame":
        redef = self.df.copy()
        redef.index = redef.index - redef.index[0]
        return self._wrap(redef)

    def lim(self, end):
        return self._wrap(self.df[self.df.index <= end].copy())

    def reduce(self, time_col='time', target_duration=10.0, target_step=0.01):
        """
        원본 시계열을 0 ~ target_duration초로 압축하고,
        target_step 간격으로 보간하여 resample한 DataFrame을 반환합니다.

        Parameters
        ----------
        time_col : str
            시간 정보가 들어 있는 컬럼명
        target_duration : float
            압축 후 전체 길이 (기본 10초)
        target_step : float
            최종 샘플링 간격 (기본 0.01초)

        Returns
        -------
        pd.DataFrame
            time_scaled 컬럼을 포함한 압축된 DataFrame
        """
        if self.df is None or len(self.df) == 0:
            return pd.DataFrame()

        df = self.df.reset_index().copy()

        # 2) 시간축 스케일링 (0 ~ target_duration)
        t_min = df[time_col].iloc[0]
        t_max = df[time_col].iloc[-1]

        if t_max == t_min:
            raise ValueError("time_col의 값이 모두 같아서 스케일링할 수 없습니다.")

        df["time_scaled"] = (df[time_col] - t_min) / (t_max - t_min) * target_duration

        # 3) 새 시간축 생성
        new_time = np.arange(0, target_duration + target_step, target_step)

        # 4) 보간
        df_interp = df.set_index("time_scaled")
        numeric_cols = df_interp.select_dtypes(include="number").columns

        # time_col도 numeric일 수 있으므로 보간 대상에서 제외
        numeric_cols = [c for c in numeric_cols if c != time_col]

        out = df_interp[numeric_cols].reindex(df_interp.index.union(new_time)).sort_index()
        out = out.interpolate(method="index")

        # 5) 새 시간축에 맞게 추출
        out = out.loc[new_time].reset_index().rename(columns={"time_scaled": "time"})
        return self._wrap(out.set_index("time"))

    def resample(
            self,
            interval: float = 0.01,
            method: str = "linear",
            limit_direction: str = "both",
    ) -> "MdfFrame":
        """
        시계열 데이터를 지정한 sampling time으로 resample

        Parameters
        ----------
        interval : float
            리샘플 간격 (초). 예: 0.01
        method : str
            보간 방식. 기본은 'linear'
        limit_direction : str
            보간 방향. 기본은 'both'

        Returns
        -------
        MdfFrame
            resample된 wrapper
        """
        df = self.df.copy()

        if df.empty:
            return self._wrap(df)

        if not isinstance(df.index, pd.Index):
            raise TypeError("DataFrame index must be time index.")

        # 시간축 생성
        start = float(df.index[0])
        end = float(df.index[-1])
        new_index = pd.Index(
            np.round(np.arange(start, end + interval / 2, interval), 10),
            name=df.index.name,
        )

        # 새 인덱스로 맞춘 뒤 보간
        reindexed = df.reindex(new_index)
        reindexed = reindexed.interpolate(method=method, limit_direction=limit_direction)
        reindexed = reindexed.ffill().bfill()

        return self._wrap(reindexed)

    def to_asc(
            self,
            file: str,
            time_col: Optional[str] = None,
            delimiter: str = "\t",
            float_format: str = "%.9f",
            sample_count_as_float: bool = True,
    ) -> None:
        """
        ETAS ASCII Item File 형식으로 저장
        """
        df = self.df.copy()

        # time 컬럼 결정
        if time_col is not None:
            if time_col not in df.columns:
                raise KeyError(f"'{time_col}' not found in DataFrame columns.")
            time = df[time_col].to_numpy()
            data = df.drop(columns=[time_col]).copy()
            time_name = time_col
        else:
            time = df.index.to_numpy()
            data = df.copy()
            time_name = df.index.name or "time"

        # index를 time으로 쓰는 경우, 이름 정리
        if time_col is None:
            data = data.reset_index(drop=True)

        # sample count
        sample_count = float(len(df)) if sample_count_as_float else len(df)

        with open(file, "w", encoding="utf-8", newline="") as f:
            # 1) header
            f.write(f"ETASAsciiItemFile{delimiter}record{delimiter}CrLf{delimiter}Tab\r\n")

            # 2) sampleCount
            f.write(f"sampleCount {sample_count}\r\n")

            # 3) channel names
            cols = [time_name] + list(data.columns)
            f.write(delimiter.join(map(str, cols)) + "\r\n")

            # 4) types
            # time은 f8, 나머지도 기본적으로 f8 처리
            types = ["f8"] * len(cols)
            f.write(delimiter.join(types) + "\r\n")

            # 5) units
            units = ['""'] * len(cols)
            f.write(delimiter.join(units) + "\r\n")

            # 6) data rows
            for i in range(len(df)):
                row = [time[i]] + [data.iloc[i, j] for j in range(data.shape[1])]
                formatted = []
                for n, v in enumerate(row):
                    fmt = "%.2f" if n == 0 else float_format
                    if isinstance(v, (int, float)):
                        formatted.append(fmt % v)
                    else:
                        formatted.append(str(v))
                f.write(delimiter.join(formatted) + "\r\n")
            f.write("\r\n")
        return

    def to_dataframe(self) -> DataFrame:
        return self.df.copy()

    def to_mdf(
        self,
        file: Optional[str] = None,
        time_col: Optional[str] = None,
        overwrite: bool = True,
        **kwargs
    ) -> MDF:

        # ASCET OFFLINE-SIMULATION = mdf v2.00: NOT WORKING
        df = self.df.copy()

        if time_col is not None:
            if time_col not in df.columns:
                raise KeyError(f"'{time_col}' not found in DataFrame columns.")
            timestamps = df[time_col].to_numpy()
            df = df.drop(columns=[time_col])
        else:
            timestamps = df.index.to_numpy()

        mdf = MDF(version=kwargs.get('version', '3.3'))
        for col in df.columns:
            signal = Signal(
                samples=df[col].to_numpy(),
                timestamps=timestamps,
                name=str(col),
            )
            mdf.append(signal)

        if file is not None:
            if os.path.exists(file) and not overwrite:
                raise FileExistsError(f"File already exists: {file}")
            mdf.save(file)

        return mdf



if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    src = r"D:\Archive\00_프로젝트\2017 통신개발-\2026\DS0601 CR18734880 OBM 인증 대응(HEV CANFD)\08_Test\0515_NX5e_48V_회사_남양주차장.mf4"
    # src = r"D:\Archive\00_프로젝트\2017 통신개발-\2026\DS0601 CR18734880 OBM 인증 대응(HEV CANFD)\08_Test\0612_NX5e_PHEV_KM_Mile_변환확인.mf4"
    rd = MdfFrame(src)
    # print(rd)
    # print(rd.columns)
    print(rd[[c for c in rd.columns if c.startswith("Can_")]])

    resample = rd[[
        "OBM_stWrnLvIndc",
        # "FD_stVehVUnit",
        "OBM_dstRemnIndc",
        "OBM_ctRemnReStrt",
        "OBM_mNoxEmiLstTrip",
        "OBM_mNoxAvgTotO2O",
        "OBM_mNoxEmiLimLegis",
        "OBM_volFuCnsPer100LstTrip",
        "OBM_volFuCnsPer100LT",
    ]]
    # print(resample.mid)
    # print(resample.mid.reindex)

    # targ = resample.mid.reindex.resample().lim(10)
    targ = resample.reduce()
    print(targ)
    # resample.mid.reindex.to_mdf(
    #     r"D:\ETASData\ASCET6.1\Export\obm.dat",
    #     version="2.00"
    # )
    targ.to_asc(
        r"D:\ETASData\ASCET6.1\Export\obm.asc"
    )




