from cannect.errors import SVNError
from cannect.utils.tools import path_abbreviate
from pandas import DataFrame
from pathlib import Path
from typing import Callable, Union
import pandas as pd
import subprocess, sqlite3
import os


class Subversion:

    logger :Callable = print
    silence:bool     = False

    @classmethod
    def read_wcdb(cls, path:Union[Path,str]) -> DataFrame:
        conn = sqlite3.connect(path)
        data = pd.read_sql_query('SELECT * FROM NODES', conn)
        conn.close()
        return data

    @classmethod
    def commit(cls, path:Union[str, Path], message:str):
        result = subprocess.run(
            ["svn", "commit", path, "-m", message],
            capture_output=True,
            text=True,
            check=True
        )

        if not cls.silence:
            cls.logger("Commit successful!")
            cls.logger(result.stdout)
        return

    @classmethod
    def log(cls, path:Union[str, Path]) -> DataFrame:
        """
        :param path: .svn 하위의 파일 또는 폴더
        :return:
        """
        result = subprocess.run(['svn', 'log', path], capture_output=True, text=True)
        if result.returncode != 0:
            raise SVNError(f'FAILED TO GET LOG: {path}')
        text = [e for e in result.stdout.split('\n') if e and (not e.endswith('-'))]
        data = []
        line = ''
        for n, part in enumerate(text):
            if n % 2:
                line = f'{line} | {part}'.split(' | ')
                data.append(line)
                line = ''
            else:
                line += part
        data = DataFrame(data=data)
        data = data.drop(columns=[3]).rename(columns={0: 'revision', 1:'author', 2: 'datetime', 4: 'log'})
        data = data[data['revision'].str.startswith('r')]
        data = data[data["log"].str.startswith('[')]
        data["datetime"] = data["datetime"].apply(lambda x: x[:x.find('+0900') - 1])
        data["log"] = data["log"].apply(lambda x: x.split('] ')[-1])
        return data

    @classmethod
    def status(cls, path:Union[str, Path]):
        try:
            result = subprocess.run(
                ['svn', 'status', str(path)],
                capture_output=True, text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise SVNError(f'FAILED TO CHECK STATUS: {path} FOR {e}')

    @classmethod
    def save_revision_to(cls, file:Union[str, Path], revision:Union[int, str], dst:Union[str, Path]=''):
        """
        :param file:
        :param revision:
        :param dst: 저장할 경로, 미입력 시 SVN 파일과 동일 경로
        :return:
        """
        # svn export -r [리비전] [파일경로/URL] [저장할경로]
        file = Path(file)
        if not dst:
            dst = file.parent
        dst = Path(dst) / file.name.replace(".zip", f"-{revision}.zip")
        command = ['svn', 'export', '-r', str(revision), file, dst, '--force']

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            if not cls.silence:
                cls.logger(f"Save {file.name} as {path_abbreviate(dst.parent)}")
        except subprocess.CalledProcessError as e:
            raise SVNError(f'FAILED TO SAVE REVISION OF {file.name}: {e}')

    @classmethod
    def update(cls, path:Union[str, Path]) -> str:
        """
        :param path: .svn 하위의 파일 또는 폴더
        :return:
        """
        path = str(path)
        if not "." in os.path.basename(path):
            path += r"\\"
        try:
            result = subprocess.run(
                ['svn', 'update', path],
                capture_output=True,
                text=True,
                check=True
            )
            msg = result.stdout[:-1]
        except subprocess.CalledProcessError as e:
            msg = f"Failed to update SVN repository: '{path}' {e.stderr}"

        if not cls.silence:
            cls.logger(msg)
        return msg



if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    # Subversion.commit(
    #     path=r"E:\SVN\dev.bsw\hkmc.ems.bsw.docs\branches\HEPG_Ver1p1\11_ProjectManagement\CAN_Database\dev\G-PROJECT_KEFICO-EMS_CANFD_r21676@01.json",
    #     message="[LEE JEHYEUK] CAN DB Commit"
    # )

    # save_revision(
    #     r"E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\CANInterface\EMS\Message\CanEMSM_CNG\CanEMSM_CNG.zip",
    #     23000,
    #     r"E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\CANInterface\EMS\Message\CanEMSM_CNG",
    # )