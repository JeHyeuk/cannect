from cannect.config import E
from cannect.core.subversion import Subversion as svn
from cannect.core.can.db2.util import excel_to_dataframe
from cannect.errors import SVNError
from cannect.utils.deco import single_arg_constraint
from cannect.utils.logger import Logger
from cannect.utils.tools import path_abbreviate

from pathlib import Path
from typing import Union
import os


class CANDBVcs(Path):
    """
    CAN DB Version Control System
    RPA를 위한 CAN DB 버전 시스템이다. json 포맷으로 구성된 데이터파일에 대한 버전이며
    pandas DataFrame과 호환한다. 데이터파일의 집합은 외부로 공개되어서는 안 되며
    구동하는 호스트내 경로를 입력하여야 한다. 경로는 환경변수로 관리하거나 HMG 보안 처리된
    서버가 Check-Out된 경로를 사용한다.
    """
    def __getitem__(self, rev:Union[int, str]):
        rev = self.check_revision(rev)
        json = [f for f in self if f.startswith(f'{self.base}_{rev}')]
        if not json:
            svn.logger(f'"{self.base} {rev}"에 해당하는 json 파일이 없습니다.')
            svn.logger(f'- 자동으로 생성합니다.')

            json = self.create(rev)
            svn.logger(f'- "{path_abbreviate(json)}"로 생성하였습니다.')
            return json

        return E.SVN_CANDB / f'dev/{json[-1]}'

    @single_arg_constraint(
        "자체제어기_KEFICO-EMS_CANFD",
        "자체제어기_KEFICO-EMS_고속CAN",
        "G-PROJECT_KEFICO-EMS_CANFD",
    )
    def __init__(self, base:str='자체제어기_KEFICO-EMS_CANFD'):
        svn.logger = console = Logger(datetime=False)

        self.base = base
        self.file = file = E.SVN_CANDB / f'{base}.xlsx'
        self.log = log = svn.log(file)

        json = [f for f in self if log.revision[0] in f]
        if not json:
            console(f'"{self.base} {log.revision[0]}"에 해당하는 json 파일이 없습니다.')
            console(f'- 자동으로 생성합니다.')

            json = self.create()
            console(f'- "{path_abbreviate(json)}"로 생성하였습니다.')
            super().__init__('_json', json)
        else:
            super().__init__('_json', E.SVN_CANDB / f'dev/{json[-1]}')

        return

    def __iter__(self):
        for f in os.listdir(E.SVN_CANDB / 'dev'):
            if f.startswith(self.base):
                yield f

    def check_revision(self, rev:Union[int, str]) -> str:
        if isinstance(rev, int) or (not rev.startswith('r')):
            rev = f'r{rev}'
        if not rev in self.log.revision.values:
            raise SVNError(f'"{self.base}.xlsx <r.{rev}>"가 없습니다. Revision을 확인하세요.')
        return rev

    def create(self, rev:Union[int, str]=''):
        if not rev:
            rev = self.log.revision[0]
            src = self.file
        else:
            rev = self.check_revision(rev)
            svn.silence = True
            svn.save_revision_to(self.file, str(rev).replace('r', ''), E.SVN_CANDB)
            src = str(self.file).replace(".xlsx", f"-{str(rev).replace('r', '')}.xlsx")

        json = [f for f in self if f.startswith(f'{self.base}_{rev}')]
        if not json:
            json = E.SVN_CANDB / f'dev/{self.base}_{rev}@01.json'
        else:
            json, count = tuple(json[-1].split('@'))
            json = E.SVN_CANDB / f'dev/{json}@{str(int(count.split('.')[0]) + 1).zfill(2)}.json'

        excel_to_dataframe(src).to_json(json, orient='index')
        return json


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    from cannect import mount
    mount(r"E:\SVN")

    vcs = CANDBVcs()
    print(vcs.name)
    print(vcs)
    print(vcs[21612])
