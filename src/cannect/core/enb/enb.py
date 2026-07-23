"""
Engineering Build
- SQLBaselineDB  : SQL Server 베이스라인 DB 접근
- PipelineEnv    : pipeline.env 파일 관리
- _JenkinsTrigger: CGEN.zip → 공용 서버 복사 + Jenkins API 빌드 트리거
- EngBuild       : 엔지니어링 빌드 메인 클래스 — 생성자 호출만으로 전 과정 완료
"""

import shutil
import sys
from pathlib import Path
from typing import Dict, Optional
from urllib import request as urllib_request
from urllib.error import URLError
import base64

try:
    import pyodbc
except ModuleNotFoundError as exc:
    pyodbc = None
    _PYODBC_IMPORT_ERROR = exc
else:
    _PYODBC_IMPORT_ERROR = None

from cannect.core.enb.config import (
    SQL_SERVER,
    SQL_DATABASE,
    SQL_UID,
    SQL_PWD,
    OFFICIAL_BUILD,
    HEX_OUTPUT_DIR,
    A2L_OUTPUT_DIR,
    PIPELINE_ENV_FILENAME,
    ASCET_CGEN_ZIP,
    JENKINS_URL,
    JENKINS_JOB_NAME,
    JENKINS_USER,
    JENKINS_API_TOKEN,
    SHARED_SERVER_BASE,
)


# ══════════════════════════════════════════════════════════════════════
# SQLBaselineDB
# ══════════════════════════════════════════════════════════════════════

class SQLBaselineDB:
    """SQL Server BaselineDB — BL_VERSION_LIST에서 베리언트별 Rev 조회"""

    def __init__(self):
        if pyodbc is None:
            raise ModuleNotFoundError(
                "pyodbc가 현재 활성 Python 환경에 없습니다. "
                f"`python -m pip install pyodbc` 를 실행해 주세요. "
                f"현재 인터프리터: {sys.executable}"
            ) from _PYODBC_IMPORT_ERROR

        self.conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={SQL_SERVER};"
            f"DATABASE={SQL_DATABASE};"
            f"UID={SQL_UID};"
            f"PWD={SQL_PWD};"
        )

    def connect(self):
        try:
            return pyodbc.connect(self.conn_str, timeout=10)
        except pyodbc.Error as e:
            raise ConnectionError(f"[ERROR] SQL Server 연결 실패: {e}")

    def fetch_variant_rev(self, variant: str) -> Dict[str, str]:
        query = """
            SELECT TOP 1
                ASCET_Project,
                BSW_Platform,
                BSW_SrcPath,
                ASCET_Project_Rev,
                BSW_Platform_Rev,
                BPM_Rev
            FROM dbo.BL_VERSION_LIST
            WHERE SW_Package_Name = ?
            ORDER BY CreateTime DESC
        """
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query, variant)
                row = cursor.fetchone()

            if row is None:
                raise ValueError(f"[ERROR] 베리언트 '{variant}' 를 DB에서 찾을 수 없습니다.")

            return {
                'ASCET_Project':     row.ASCET_Project,
                'BSW_Platform':      row.BSW_Platform,
                'BSW_SrcPath':       row.BSW_SrcPath,
                'ASCET_Project_Rev': row.ASCET_Project_Rev,
                'BSW_Platform_Rev':  row.BSW_Platform_Rev,
                'BPM_Rev':           row.BPM_Rev,
            }
        except pyodbc.Error as e:
            raise ConnectionError(f"[ERROR] DB 쿼리 실행 실패: {e}")


# ══════════════════════════════════════════════════════════════════════
# PipelineEnv
# ══════════════════════════════════════════════════════════════════════

class PipelineEnv:
    """pipeline.env 파일 생성 및 관리"""

    def __init__(self, variant: str, rev_info: Dict[str, any]):
        self.variant  = variant
        self.rev_info = rev_info
        self.env_dict = self._build_env_dict()

    def _build_env_dict(self) -> Dict[str, str]:
        return {
            'VARIANT':        self.variant,
            'ASW_PROJECT':    self.rev_info['ASCET_Project'],
            'BSW_PLATFORM':   self.rev_info['BSW_Platform'],
            'BSW_SRC_PATH':   self.rev_info['BSW_SrcPath'],
            'ASW_REV':        str(self.rev_info['ASCET_Project_Rev']),
            'BSW_REV':        str(self.rev_info['BSW_Platform_Rev']),
            'BPM_REV':        str(self.rev_info['BPM_Rev']),
            'OFFICIAL':       'false' if not OFFICIAL_BUILD else 'true',
            'HEX_OUTPUT_DIR': HEX_OUTPUT_DIR,
            'A2L_OUTPUT_DIR': A2L_OUTPUT_DIR,
        }

    def write(self, output_path: Optional[str] = None) -> Path:
        if output_path is None:
            output_path = Path("build") / PIPELINE_ENV_FILENAME
        else:
            output_path = Path(output_path)
            if output_path.parent == Path("."):
                output_path = Path("build") / output_path.name

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for key, value in self.env_dict.items():
                f.write(f"{key}={value}\n")

        return output_path

    def to_dict(self) -> Dict[str, str]:
        return self.env_dict.copy()

    def __repr__(self):
        return (
            f"PipelineEnv(variant='{self.variant}', "
            f"ASW_REV={self.rev_info['ASCET_Project_Rev']}, "
            f"BSW_REV={self.rev_info['BSW_Platform_Rev']})"
        )


# ══════════════════════════════════════════════════════════════════════
# _JenkinsTrigger
# ══════════════════════════════════════════════════════════════════════

class _JenkinsTrigger:
    r"""
    CGEN.zip → 공용 서버 복사 + Jenkins 빌드 API 호출

    흐름:
        1. HNB_UNDEFINED.zip 존재 확인
        2. \\kefico\keti\ENT_Engine_mgt\Temp\Jenkins\{client_id}\CGEN.zip 으로 복사
        3. Jenkins buildWithParameters API POST 호출
    """

    def __init__(self, client_id: str, variant: str, zip_path: Optional[str] = None):
        self.client_id = client_id
        self.variant   = variant
        self.zip_src   = Path(zip_path or ASCET_CGEN_ZIP)
        self.zip_dst   = Path(SHARED_SERVER_BASE) / client_id / "CGEN.zip"

    def trigger(self) -> None:
        print(f"[JenkinsTrigger] zip 원본   : {self.zip_src}")
        print(f"[JenkinsTrigger] 업로드 대상: {self.zip_dst}")

        self._validate()
        self._copy_zip()
        self._call_jenkins()

    def _validate(self):
        if not self.zip_src.exists():
            raise FileNotFoundError(
                f"[JenkinsTrigger] ASCET CodeGen zip 없음: {self.zip_src}\n"
                f"  ASCET 6.1에서 코드젠을 먼저 실행해 주세요."
            )

    def _copy_zip(self):
        self.zip_dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"[JenkinsTrigger] CGEN.zip 복사 중...")
        shutil.copy2(self.zip_src, self.zip_dst)
        print(f"[JenkinsTrigger] ✅ 복사 완료 → {self.zip_dst}")

    def _call_jenkins(self):
        url = (
            f"{JENKINS_URL}/job/{JENKINS_JOB_NAME}/buildWithParameters"
            f"?token={JENKINS_API_TOKEN}"
            f"&VARIANT={self.variant}"
            f"&EMP_ID={self.client_id}"
        )

        credentials = base64.b64encode(
            f"{JENKINS_USER}:{JENKINS_API_TOKEN}".encode()
        ).decode()

        req = urllib_request.Request(
            url,
            method="POST",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type":  "application/x-www-form-urlencoded",
            },
        )

        print(f"[JenkinsTrigger] Jenkins API 호출 중...")
        print(f"[JenkinsTrigger] POST {JENKINS_URL}/job/{JENKINS_JOB_NAME}/buildWithParameters")
        print(f"[JenkinsTrigger]   VARIANT={self.variant}, EMP_ID={self.client_id}")

        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except URLError as e:
            raise ConnectionError(
                f"[JenkinsTrigger] Jenkins 연결 실패: {e}\n"
                f"  Jenkins가 켜져있는지 확인하세요: {JENKINS_URL}"
            )

        if status in (200, 201):
            print(f"[JenkinsTrigger] ✅ Jenkins 빌드 트리거 성공 (HTTP {status})")
        else:
            raise RuntimeError(
                f"[JenkinsTrigger] 예상치 못한 응답 코드: {status}"
            )


# ══════════════════════════════════════════════════════════════════════
# EngBuild
# ══════════════════════════════════════════════════════════════════════

class EngBuild:
    """
    엔지니어링 빌드 메인 클래스
    """

    def __init__(self, variant: str, client_id: str):
        if not variant:
            raise ValueError("베리언트명이 필요합니다.")
        if not client_id:
            raise ValueError("사용자 ID(client_id)가 필요합니다.")

        self.variant      = variant
        self.client_id    = client_id
        self.rev_info     = None
        self.pipeline_env = None
        self.env_file     = None

        self._run()

    def to_dict(self) -> Dict[str, str]:
        return self.pipeline_env.to_dict()

    def __repr__(self):
        if self.rev_info is None:
            return f"EngBuild(variant='{self.variant}', fetched=False)"
        return (
            f"EngBuild(variant='{self.variant}', "
            f"ASW_REV={self.rev_info['ASCET_Project_Rev']}, "
            f"BSW_REV={self.rev_info['BSW_Platform_Rev']}, "
            f"BPM_REV={self.rev_info['BPM_Rev']})"
        )

    def _run(self):
        # 1) DB 조회
        print(f"[EngBuild] 베리언트: {self.variant}")
        print("[EngBuild] DB 조회 중...")
        db                = SQLBaselineDB()
        self.rev_info     = db.fetch_variant_rev(self.variant)
        self.pipeline_env = PipelineEnv(self.variant, self.rev_info)
        print(f"[EngBuild] ✅ {self}")

        # 2) pipeline.env 생성
        self.env_file = self.pipeline_env.write()
        print(f"[EngBuild] pipeline.env 생성: {self.env_file}")

        # 3) CGEN.zip 업로드 + Jenkins 트리거
        trigger = _JenkinsTrigger(
            client_id = self.client_id,
            variant   = self.variant,
        )
        trigger.trigger()
        print(f"[EngBuild] ✅ 완료 — Jenkins 빌드가 곧 시작됩니다.")


# ── 직접 실행 테스트 ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("[INFO] EngBuild 테스트 시작...\n")
    builder = EngBuild("TX4T9MTN9LDT", client_id="22011113")
    print(f"\n[INFO] 환경변수:\n")
    for k, v in builder.to_dict().items():
        print(f"  {k}={v}")
