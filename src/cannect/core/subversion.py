import os, subprocess, sqlite3
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path, WindowsPath, PosixPath
from typing import Union, List, Optional
from datetime import datetime

# OS에 따른 Path 클래스 선택
ParentPath = WindowsPath if Path().name == '' and Path.drive else PosixPath
if not issubclass(Path, ParentPath):  # 일반적인 경우
    ParentPath = type(Path())


class SubVersion(Path):
    """
    pathlib.Path를 상속받아 SVN 기능을 확장한 클래스.
    기존 Path의 모든 기능(exists, join, / 연산 등)을 그대로 사용 가능합니다.
    """

    def __new__(cls, *args):
        # Path 객체 생성을 위한 표준 방식
        return super().__new__(cls, *args)

    def __init__(self, *args):
        # Path는 불변 객체이므로 속성 초기화 시 주의
        super().__init__(*args)
        self._db_cache = None

    def __truediv__(self, key):
        # / 연산자 사용 시 반환 타입을 SubVersion으로 유지
        return SubVersion(super().__truediv__(key))

    def __getitem__(self, key: str):
        """이름으로 하위 파일/폴더 검색 (기존 기능 유지)"""
        db = self.inventory
        if db.empty:
            return None

        search_key = key.replace('\\', '/')
        matches = db[db['path'].str.endswith(search_key, na=False)]['path'].tolist()

        if not matches:
            return None
        return SubVersion(matches[0]) if len(matches) == 1 else [SubVersion(f) for f in matches]

    @property
    def inventory(self) -> pd.DataFrame:
        """현재 경로 또는 상위 경로의 .svn DB를 찾아 인벤토리 반환"""
        if self._db_cache is not None:
            return self._db_cache

        # 현재 위치부터 상위로 올라가며 .svn 폴더 탐색
        svn_root = self
        while svn_root.parent != svn_root:
            if (svn_root / ".svn").is_dir():
                break
            svn_root = svn_root.parent

        db_path = svn_root / ".svn" / "wc.db"
        if not db_path.exists():
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            query = """
                    SELECT local_relpath as relpath, kind, changed_revision as revision, 
                           changed_author as author, changed_date as date
                    FROM NODES WHERE presence = 'normal'
                    """
            df = pd.read_sql_query(query, conn)
            conn.close()

            if not df.empty:
                root_posix = svn_root.as_posix()
                df['date'] = pd.to_datetime(df['date'], unit='us', errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")
                df['path'] = df['relpath'].apply(lambda x: f"{root_posix}/{x}" if x else root_posix)
                self._db_cache = df
                return df
        except Exception as e:
            print(f"DB Query Error: {e}")

        return pd.DataFrame()

    def _command(self, args: List[str]) -> str:
        # self 자체가 Path이므로 바로 사용
        target_cwd = self if self.is_dir() else self.parent
        full_cmd = ["svn"] + args
        try:
            result = subprocess.run(
                full_cmd,
                cwd=str(target_cwd),
                capture_output=True,
                text=False,
                check=True
            )
            parts, flag = [], False
            for part in str(target_cwd).split(os.sep):
                if part.lower() == 'svn':
                    flag = True
                    part = "%svn%"
                if flag:
                    parts.append(part)

            try:
                return result.stdout.decode('utf-8') \
                       .replace("'.'", f"'{os.sep.join(parts)}'")
            except UnicodeDecodeError:
                return result.stdout.decode('cp949', errors='replace')
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('cp949', errors='replace')
            print(f"[{datetime.now()}] SVN Error: {err_msg}")
            raise Exception(err_msg)

    # --- SVN Methods ---
    def update(self):
        return self._command(["update", self.as_posix()])

    def commit(self, message: str):
        return self._command(["commit", "-m", f'"{message}"', self.as_posix()])

    def add(self):
        return self._command(["add", "--parents", self.as_posix()])

    def log(self, limit: int = 10) -> pd.DataFrame:
        xml_content = self._command(["log", "--xml", "-l", str(limit), self.as_posix()])
        root_node = ET.fromstring(xml_content)
        data = [{
            "revision": entry.get('revision'),
            "author": entry.findtext('author'),
            "date": entry.findtext('date'),
            "message": entry.findtext('msg')
        } for entry in root_node.findall('logentry')]

        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.strftime("%Y-%m-%d %H:%M:%S")
        return df

    def save_revision_as(self, revision: Union[int, str], output_path: Union[str, Path]):
        out = Path(output_path).resolve()
        return self._command([
            "export",
            "--force",
            "-r", str(revision),
            self.as_posix(),
            out.as_posix()
        ])

    # --- Properties (Shortcuts) ---
    @property
    def CAN(self):
        return self / 'dev.bsw/hkmc.ems.bsw.docs/branches/HEPG_Ver1p1/11_ProjectManagement'

    @property
    def CANDB(self):
        return self.CAN / 'CAN_Database'

    @property
    def CONF(self):
        return self / 'GSL_Build/1_AswCode_SVN/PostAppSW/0_XML/DEM_Rename'

    @property
    def HISTORY(self):
        return self / 'GSL_Release/4_SW변경이력'

    @property
    def IR(self):
        return self / 'GSL_Build/8_IntegrationRequest'

    @property
    def MODEL(self):
        return self / 'model'

    @property
    def SDD(self):
        return self / 'GSL_Build/7_Notes'

    @property
    def UNECE(self):
        return self / 'Autron_CoWork/사이버보안/Module_Test_Results'


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    SVN = SubVersion(r"E:\SVN")
    # print(SVN)
    # print(SVN.CONF)
    # print(SVN.HISTORY)
    # print(SVN.IR)
    # print(SVN.MODEL)
    # print(SVN.UNECE)
    # print(SVN.MODEL.inventory)
    # print(SVN.MODEL['CanFDCCUM.zip'], type(SVN.MODEL['CanFDCCUM.zip']))
    # print(SVN.MODEL['LinM.zip'])
    # print(SVN.MODEL['LinM/LinM.zip'])
    # print(SVN.MODEL['CanFDCCUM.zip'].log())
    # res = SVN.CAN['자체제어기_KEFICO-EMS_고속CAN.xlsx'].commit('[JEHYEUK.LEE]')
    # print(res)