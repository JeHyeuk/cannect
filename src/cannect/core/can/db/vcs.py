from cannect.config import env
from cannect.core.can.db.schema import standardize
from cannect.core.subversion import Subversion
from cannect.errors import CANDBError
from cannect.utils.excel import ComExcel
from cannect.utils.tools import path_abbreviate

from datetime import datetime
from pandas import DataFrame
from pathlib import Path
from pyperclip import paste
from typing import Callable
import os


class CANDBVcs:
    """
    CAN DB Version Control System
    RPA를 위한 CAN DB 버전 시스템이다. json 포맷으로 구성된 데이터파일에 대한 버전이며
    pandas DataFrame과 호환한다. 데이터파일의 집합은 외부로 공개되어서는 안 되며
    구동하는 호스트내 경로를 입력하여야 한다. 경로는 환경변수로 관리하거나 HMG 보안 처리된
    서버가 Check-Out된 경로를 사용한다.
    """
    silence :bool     = False
    logger  :Callable = print

    def __init__(self, filename:str=''):
        if not filename:
            filename = "자체제어기_KEFICO-EMS_CANFD.xlsx"
        filepath = env.SVN_CANDB / filename
        if not filepath.exists():
            raise CANDBError(f'{filename} NOT EXISTS')

        self.name     = '.'.join(filename.split(".")[:-1])
        self.filename = filename
        self.filepath = filepath
        self.history  = history = Subversion.log(filepath)
        self.revision = history.iloc[0, 0]
        return

    def _find_jsons(self) -> DataFrame:
        data = []
        for file in os.listdir((env.SVN_CANDB / "dev")):
            if not file.endswith('.json'):
                continue
            if file.startswith(self.name) and file.endswith('.json'):
                path = env.SVN_CANDB / f'dev/{file}'
                data.append({
                    'revision': file.split("_")[-1].replace(".json", ""),
                    'datetime': datetime.fromtimestamp(os.path.getmtime(path)),
                    'name': file,
                    'path': path,
                })
        return DataFrame(data=data)

    @property
    def json(self) -> Path:
        """
        Excel CAN DB에 대한 최신 json 파일의 경로
        :return:
        """
        jsons = self._find_jsons()
        if jsons.empty:
            raise CANDBError(f'NO MATCHED JSON DB FOR {{{self.filename}}} IN SVN')

        jsons = jsons[jsons['name'].str.startswith(f'{self.name}_{self.revision}')] \
                .sort_values(by='revision', ascending=False)
        if jsons.empty:
            raise CANDBError(f'NO MATCHED JSON DB FOR {{{self.filename}}} @{{{self.revision}}} IN SVN')
        return Path(jsons.iloc[0]['path'])

    def to_json(self, mode:str='auto'):
        if mode == 'auto':
            xl = ComExcel(self.filepath)
            xl.ws.UsedRange.Copy()

        try:
            jsonpath = self.json
            rev = str(int(jsonpath.name.split("@")[-1].split(".")[0]) + 1).zfill(2)
            jsonpath = jsonpath.parent / f"{self.name}_{self.revision}@{rev}.json"
        except CANDBError:
            jsonpath = env.SVN_CANDB / f'dev/{self.name}_{self.revision}@01.json'

        clipboard = [row.split("\t") for row in paste().split("\r\n")]
        source = DataFrame(data=clipboard[1:], columns=standardize(clipboard[0]))
        source = source[~source["ECU"].isna() & (source["ECU"] != "")]
        source.to_json(jsonpath, orient='index')
        if not self.silence:
            self.logger("Manually Updated CAN DB from clipboard.")
            self.logger(f"- Saved as : {path_abbreviate(jsonpath)}")
        return

    # def commit_json(self):
    #     Subversion.commit(self.json, message="[CANNECT] AUTO-COMMIT CAN JSON DB")
    #     return

if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    cdb = CANDBVcs()
    # cdb = CANDBVcs(r"G-PROJECT_KEFICO-EMS_CANFD.xlsx")
    cdb.to_json()
    print(cdb.json)
    # cdb.commit_json()
