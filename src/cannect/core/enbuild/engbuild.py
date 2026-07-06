"""
Engineering Build
- SQLBaselineDB : SQL Server 베이스라인 DB 접근
- PipelineEnv   : pipeline.env 파일 관리
- _CGenPusher   : HNB_UNDEFINED.zip 압축 해제 + GitLab push
- EngBuild      : 엔지니어링 빌드 메인 클래스 — 생성자 호출만으로 전 과정 완료
"""

import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    import pyodbc
except ModuleNotFoundError as exc:
    pyodbc = None
    _PYODBC_IMPORT_ERROR = exc
else:
    _PYODBC_IMPORT_ERROR = None

from .config import (
    SQL_SERVER,
    SQL_DATABASE,
    SQL_UID,
    SQL_PWD,
    OFFICIAL_BUILD,
    HEX_OUTPUT_DIR,
    A2L_OUTPUT_DIR,
    PIPELINE_ENV_FILENAME,
    ASCET_CGEN_ZIP,
    GITLAB_LOCAL_REPO,
    GITLAB_CGEN_SUBDIR,
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
            'BSW_SRC_PATH':  self.rev_info['BSW_SrcPath'],
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
# _CGenPusher  (내부 전용 — 직접 import 불필요)
# ══════════════════════════════════════════════════════════════════════

class _CGenPusher:
    """
    ASCET CodeGen 결과물 GitLab Push

    흐름:
        1. HNB_UNDEFINED.zip 존재 확인
        2. repo/cgen/ 초기화 후 zip 압축 해제
        3. pipeline.env → repo 루트 복사
        4. git add → commit → push
    """

    def __init__(
        self,
        zip_path:    Optional[str] = None,
        repo_path:   Optional[str] = None,
        cgen_subdir: Optional[str] = None,
    ):
        self.zip_path  = Path(zip_path   or ASCET_CGEN_ZIP)
        self.repo_path = Path(repo_path  or GITLAB_LOCAL_REPO)
        self.cgen_dir  = self.repo_path / (cgen_subdir or GITLAB_CGEN_SUBDIR)

    def push(self, pipeline_env_path: Optional[Path] = None,
             commit_msg: Optional[str] = None) -> None:

        print(f"[CGenPusher] zip    : {self.zip_path}")
        print(f"[CGenPusher] repo   : {self.repo_path}")
        print(f"[CGenPusher] cgen/  : {self.cgen_dir}")

        self._validate()
        self._extract_zip()

        if pipeline_env_path is not None:
            self._copy_pipeline_env(pipeline_env_path)

        self._git_push(commit_msg or self._auto_commit_msg())
        print("[CGenPusher] ✅ GitLab push 완료")

    # ── 내부 헬퍼 ──────────────────────────────────────────────────

    def _validate(self):
        if not self.zip_path.exists():
            raise FileNotFoundError(
                f"[CGenPusher] zip 없음: {self.zip_path}"
            )
        if not self.repo_path.exists():
            raise FileNotFoundError(
                f"[CGenPusher] repo 경로 없음: {self.repo_path}"
            )
        if not (self.repo_path / ".git").exists():
            raise EnvironmentError(
                f"[CGenPusher] .git 없음 — git clone 경로인지 확인: {self.repo_path}"
            )

    def _extract_zip(self):
        if self.cgen_dir.exists():
            shutil.rmtree(self.cgen_dir)
            print(f"[CGenPusher] 기존 cgen/ 삭제")
        self.cgen_dir.mkdir(parents=True, exist_ok=True)

        print("[CGenPusher] zip 압축 해제 중...")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            zf.extractall(self.cgen_dir)
        print(f"[CGenPusher] 압축 해제 완료 → {self.cgen_dir}")

    def _copy_pipeline_env(self, src: Path):
        dst = self.repo_path / PIPELINE_ENV_FILENAME
        shutil.copy2(src, dst)
        print(f"[CGenPusher] pipeline.env 복사 → {dst}")

    def _git_push(self, commit_msg: str):
        for cmd in [
            ["git", "add", "."],
            ["git", "commit", "-m", commit_msg],
            ["git", "push"],
        ]:
            print(f"[CGenPusher] $ {' '.join(cmd)}")
            r = subprocess.run(
                cmd, cwd=self.repo_path,
                capture_output=True, text=True, encoding="utf-8",
            )
            if r.stdout: print(r.stdout.strip())
            if r.stderr: print(r.stderr.strip())
            if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
                raise RuntimeError(
                    f"[CGenPusher] 명령 실패: {' '.join(cmd)}\n{r.stderr}"
                )

    @staticmethod
    def _auto_commit_msg() -> str:
        return f"[FACA] ASCET CodeGen push {datetime.now().strftime('%Y%m%d_%H%M%S')}"


# ══════════════════════════════════════════════════════════════════════
# EngBuild
# ══════════════════════════════════════════════════════════════════════

class EngBuild:
    """
    엔지니어링 빌드 메인 클래스

    생성자 호출 한 번으로 전 과정 자동 완료:
        DB 조회 → pipeline.env 생성 → zip 압축 해제 → GitLab push

    Usage:
        EngBuild("TX4T9MTN9LDT")
    """

    def __init__(self, variant: str):
        if not variant:
            raise ValueError("베리언트명이 필요합니다")

        self.variant      = variant
        self.rev_info     = None
        self.pipeline_env = None
        self.env_file     = None

        # ── 전 과정 자동 실행 ──
        self._run()

    # ── Public (조회용) ──────────────────────────────────────────────

    def to_dict(self) -> Dict[str, str]:
        """생성된 환경변수 딕셔너리 반환"""
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

    # ── Private ─────────────────────────────────────────────────────

    def _run(self):
        """DB 조회 → pipeline.env → GitLab push"""

        # 1) DB 조회
        print(f"[EngBuild] 베리언트: {self.variant}")
        print("[EngBuild] DB 조회 중...")
        db = SQLBaselineDB()
        self.rev_info     = db.fetch_variant_rev(self.variant)
        self.pipeline_env = PipelineEnv(self.variant, self.rev_info)
        print(f"[EngBuild] ✅ {self}")

        # 2) pipeline.env 생성
        self.env_file = self.pipeline_env.write()
        print(f"[EngBuild] pipeline.env 생성: {self.env_file}")

        # 3) zip 해제 + GitLab push
        pusher = _CGenPusher()
        pusher.push(pipeline_env_path=self.env_file)


# ── 직접 실행 테스트 ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("[INFO] EngBuild 테스트 시작...\n")
    builder = EngBuild("TX4T9MTN9LDT")   # 한 줄로 전 과정 완료
    print(f"\n[INFO] 환경변수:\n")
    for k, v in builder.to_dict().items():
        print(f"  {k}={v}")
