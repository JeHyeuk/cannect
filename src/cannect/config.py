from cannect.schema.datadictionary import DataDictionary
from cannect.errors import InternalServerError
from datetime import datetime
from pathlib import Path
import os, psutil


__namespace__ = {
    "21301106": "김남균",
    "22011005": "강지원",
    "22011029": "김병욱",
    "22011032": "김성령",
    "22011033": "김성호",
    "22011057": "김한솔",
    "22011072": "문병헌",
    "22011085": "박원진",
    "22011110": "안성웅",
    "22011115": "양웅",
    "22011133": "이동훈",
    "22403040": "이승욱",
    "22011148": "이제혁",
    "22011154": "이진노",
    "22011160": "임동훈",
    "22403041": "조규나",
    "22011187": "조재형",
    "22011206": "한대성"
}


E = ENV = env = DataDictionary(**os.environ)
E.COMPANY   = "HYUNDAI KEFICO Co.,Ltd."
E.COPYRIGHT = f'Copyright {E.COMPANY} 2020-{datetime.now().year}. All rights reserved.'
E.DIVISION  = "ELECTRIFICATION PT CONTROL TEAM 1"
E.KOREANAME = __namespace__.get(E.USERNAME, '알 수 없음')


def mount(svn_path=None):
    """
    cannect 사용자 초기 환경 설정(Configuration)
    - KEFICO 도메인이 아닌 경우 오류 표출
    - KEFICO 서버 접근 권한 및 SVN 권한 확인
    - 전역 환경 변수 설정
    :return:
    """
    global E

    if svn_path is None:
        svn_path = Path(r"\\kefico\keti\ENT\SDT\SVN")
    else:
        svn_path = Path(svn_path)

    # 운영 환경; KEFICO 도메인 확인
    if not (
        E.get('USERDNSDOMAIN', '') == 'KEFICO.GLOBAL' and
        E.get('USERDOMAIN', '') == 'HKEFICO' and
        E.get('USERDOMAIN_ROAMINGPROFILE', '') == 'HKEFICO'
    ):
        raise PermissionError(f'USER: {E.get("USERNAME")} NOT AUTHORIZED')

    # 전역 환경 변수 설정
    E.DOWNLOADS   = E.USERPROFILE / 'Downloads'
    E.SVN         = svn_path
    E.SVN_CAN     = svn_path / 'dev.bsw/hkmc.ems.bsw.docs/branches/HEPG_Ver1p1/11_ProjectManagement'
    E.SVN_CANDB   = E.SVN_CAN / 'CAN_Database'
    E.SVN_CONF    = svn_path / 'GSL_Build/1_AswCode_SVN/PostAppSW/0_XML/DEM_Rename'
    E.SVN_HISTORY = svn_path / 'GSL_Release/4_SW변경이력'
    E.SVN_IR      = svn_path / 'GSL_Build/8_IntegrationRequest'
    E.SVN_MODEL   = svn_path / 'model'
    E.SVN_UNECE   = svn_path / 'Autron_CoWork/사이버보안/Module_Test_Results'
    E.SVN_SDD     = svn_path / 'GSL_Build/7_Notes'
    for p in psutil.disk_partitions():
        if (Path(p.device) / "ETASData").exists():
            E.ETAS = Path(p.device) / "ETASData"
            if (E.ETAS / "ASCET6.1").exists():
                E.ASCET = Path(E.ETAS / "ASCET6.1")

    # 접근 권한 1차 확인; KEFICO 서버 권한 확인
    for key, path in E.items():
        if key.startswith("SVN"):
            if not path.exists():
                raise InternalServerError(f"{{{path}}} NOT EXIST IN {E.COMPANY} SERVER")

    return


if __name__ == "__main__":
    print(env.KOREANAME)
    print(env.TEMP)
    print(env.USERPROFILE / 'Downloads')
    print(env.SVN)
    print(env.SVN_CAN)
    print(env.SVN_CANDB)
    print(env.SVN_SDD)
    print(env.ETAS)
    print(env.ASCET)
    # print(env)