from cannect.config import env
from cannect.core.subversion import SubVersion
from cannect.utils.tools import unzip, zip
from pandas import DataFrame
from pathlib import Path
from datetime import datetime
import string, re


SVN = SubVersion(env.SVN_PATH)
class SddRW:

    @classmethod
    def decode_rtf(cls, rtf_content):
        """RTF 내부의 유니코드 및 CP949 16진수 코드를 한글로 복원하고 서식을 제거합니다."""

        # 1. RTF 유니코드 에스케이프 (\u12345? 또는 \u-12345?) 복원
        # RTF 유니코드는 16비트 부호 있는 정수(음수 가능)로 표현되며 뒤에 대체 문자(보통 '?')가 붙습니다.
        def unicode_replace(match):
            val = int(match.group(1))
            if val < 0:
                val += 65536  # 음수 값을 부호 없는 16비트 정수로 변환
            try:
                return chr(val)
            except ValueError:
                return ""

        # \u숫자 뒤에 오는 대체 문자 1글자(보통 '?')까지 함께 매칭하여 실제 한글로 치환
        text = re.sub(r"\\u(-?\d+).", unicode_replace, rtf_content)
        text = re.sub(r"\\u(-?\d+)", unicode_replace, text)

        # 2. RTF 16진수 에스케이프 (\'c7\'d1 등) 복원 (CP949 한글 처리)
        # 연속된 16진수 바이트 코드를 모아서 한 번에 CP949로 디코딩합니다.
        hex_pattern = re.compile(r"((?:\\'[0-9a-fA-F]{2})+)")

        def hex_replace(match):
            hex_str = match.group(1).replace("\\'", "")
            try:
                # 한국어 윈도우 RTF는 보통 CP949 인코딩을 사용합니다.
                return bytes.fromhex(hex_str).decode("cp949")
            except Exception:
                try:
                    return bytes.fromhex(hex_str).decode("utf-8", errors="ignore")
                except Exception:
                    return ""

        text = hex_pattern.sub(hex_replace, text)

        # 3. RTF 서식 태그 제거
        # 줄바꿈 태그(\par, \line)는 실제 줄바꿈(\n)으로 변경
        text = re.sub(r"\\(par|line)\b", "\n", text)
        # 나머지 컨트롤 워드 제거 (\f0, \fs24 등)
        text = re.sub(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?", "", text)
        # 중괄호 { } 제거
        text = re.sub(r"[{}]", "", text)

        return text.replace("?", "")

    @classmethod
    def _encode_rtf(cls, text: str, fallback: str = "?") -> str:
        out = []
        for ch in text:
            if ch in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] or \
                    ch in ["[", "]", ".", ",", "-", "_", ">", "<", " "] or \
                    ch.lower() in string.ascii_lowercase:
                out.append(ch)
            elif ch == '\n':
                out.append(r'\r\n')
            else:
                code = ord(ch)
                code = str(code)
                out.append(f"\\u{code}{fallback}")
        return "".join(out)

    @classmethod
    def read_rtf(cls, file_path):
        """파일 인코딩 오류를 방지하기 위해 여러 인코딩으로 읽기를 시도합니다."""
        # 한국어 윈도우 환경의 기본 인코딩인 cp949로 먼저 시도
        try:
            with open(file_path, "r", encoding="cp949", errors='ignore') as f:
                return f.read()
        except UnicodeDecodeError:
            pass

        # 실패 시 utf-8로 시도
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            pass

        # 둘 다 실패 시 바이트 손실이 없는 latin-1로 읽음 (RTF 제어문자는 모두 ASCII 영역이므로 안전)
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()

    @classmethod
    def get_ver(cls, context:str):
        if not ("[" in context and "]" in context):
            return ""
        return context[context.find("[")+1 : context.find("]")]


    def __init__(self, model:str, oid:str, **kwargs):
        """
        :param model: ASCET 모델 이름
        :param oid: SDD 노트 이름(ASCET 모델 Object ID)
        """
        self.model = model.replace("%", "")
        self.name = name = oid.replace('.zip', '') if oid.endswith('.zip') else oid
        self.svn = svn = SVN.SDD[f'{name}.zip']
        path = Path(kwargs.get('path', env.SERVER_TEMP))
        if self.svn is None:
            self.rtf = path / f'{oid}/FunctionDefinition.rtf'
            self.rtf.parent.mkdir(parents=True, exist_ok=True)
            self.content = self.write(**kwargs)
        else:
            unzip(str(svn), path)
            self.rtf = rtf = next(
                (path / name).rglob('FunctionDefinition.rtf'),
                None
            )
            self.content = self.decode_rtf(self.read_rtf(rtf))
        return

    def __iter__(self):
        for line in self.content.splitlines():
            yield line.strip()  # 앞뒤 공백 제거

    def __str__(self):
        return self.content

    @property
    def created_by(self) -> str:
        try:
            for l in self:
                if "createby" in l:
                    return l.replace("createby", "").strip()
            return env.USERNAME
        except (AttributeError, Exception):
            return env.USERNAME

    @property
    def created_date(self) -> str:
        try:
            for l in self:
                if "createdate" in l:
                    return l.replace("createdate", "").strip()
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except (AttributeError, Exception):
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def desc(self):
        ver = self.ver
        get = False
        obj = []
        for l in self:
            if ver in l:
                get = not get
                continue
            if get:
                if obj and obj[-1] == l:
                    continue
                obj.append(l)
        if obj[-1] in ["", " ", "\n"]:
            obj = obj[:-1]
        return "\n".join(obj[:-1])

    @property
    def log(self) -> DataFrame:
        data = []
        for l in self:
            if "[" in l and "]" in l:
                ver = self.get_ver(l)
                log = l[l.find(']')+1:].strip()
                if log:
                    data.append((ver, log))
        return DataFrame(data, columns=['ver', 'log'])

    @property
    def ver(self) -> str:
        try:
            return self.log.iloc[0, 0]
        except AttributeError:
            return '00.00.001'

    def write(self, **kwargs):
        time = datetime.now().strftime('%Y-%m-%d %H%M%S')
        text = rf"""{{\rtf1\ansi\deff0\uc1\ansicpg949\deftab720{{\fonttbl{{\f0\fnil\fcharset1 Arial;}}{{\f1\fnil\fcharset2 Wingdings;}}{{\f2\fnil\fcharset2 Symbol;}}}}{{\colortbl\red0\green0\blue0;\red255\green0\blue0;\red0\green128\blue0;\red0\green0\blue255;\red255\green255\blue0;\red255\green0\blue255;\red128\green0\blue128;\red128\green0\blue0;\red0\green255\blue0;\red0\green255\blue255;\red0\green128\blue128;\red0\green0\blue128;\red255\green255\blue255;\red192\green192\blue192;\red128\green128\blue128;\red0\green0\blue0;}}\wpprheadfoot1\paperw11906\paperh16838\margl567\margr624\margt850\margb850\headery720\footery720\endnhere\sectdefaultcl{{\*\generator WPTools_6.250;}}{{\*\userprops {{\propname oid}}\proptype30{{\staticval 040g1j9410g01q871c90dpcrfer3k}}
{{\propname userid}}\proptype30{{\staticval {env.USERNAME}}}
{{\propname filename}}\proptype30{{\staticval FunctionDefinition.rtf}}
{{\propname createby}}\proptype30{{\staticval {kwargs.get('created_by', self.created_by)}}}
{{\propname createdate}}\proptype30{{\staticval {kwargs.get('created_date', self.created_date)}}}
{{\propname updateby}}\proptype30{{\staticval {env.USERNAME}}}
{{\propname updatedate}}\proptype30{{\staticval {time}}}
}}{{\plain\f0\fs20 %{self.model} [{kwargs.get('ver', '00.00.001')}]\par
\pard\plain\plain\f0\fs20\par
\plain\f0\fs20 {self._encode_rtf(kwargs.get('desc', "모델 설명 없음"))}\par
\pard\plain\plain\f0\fs20\par
\plain\f0\fs20\u9654 ?\u48320 ?\u44221 ?\u45236 ?\u50669 ?\par
{kwargs.get('log', '\\plain\\f0\\fs20 [00.00.001] Initial Release\\par')}
}}}}"""
        self.content = self.decode_rtf(text)
        with open(self.rtf, 'w', encoding="ansi") as f:
            f.write(text)
        return text

    def update(self, log:str):
        newv = '00.00.001'
        objs = []
        for n, (v, l) in enumerate(self.log.itertuples(index=False)):
            if not n:
                vs = v.split(".")
                newv = f"{'.'.join(vs[:-1])}.{str(int(vs[-1]) + 1).zfill(3)}"
                objs.append(f"\\plain\\f0\\fs20 [{newv}] {self._encode_rtf(log)}\\par")
            objs.append(f"\\plain\\f0\\fs20 [{v}] {self._encode_rtf(l)}\\par")
        self.write(ver=newv, desc=self.desc, log="\n".join(objs))
        return

    def commit(self):
        file = zip(self.rtf.parent, outer=True, overwrite=True)
        # TODO
        return


if __name__ == "__main__":
    # sdd = SddRW('CanFDCCUM', '040g00002u801po70cdg7unbg5e08')
    sdd = SddRW('CatPrg', '040g030000001mo710404mgdpcd70')
    # sdd = SddRW('CatSet', '040g030000001mo71050qdbcitv9u')
    # sdd = SddRW('CatFMd', '040g030000001n870gcg3qb7l5ji2')
    # sdd = SddRW('CanFDNEWM', '040g00002u801p12345678912345d', created_by=env.USERNAME, created_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # print(sdd)
    # print("-" * 100)
    print(sdd.ver)
    print(sdd.log)
    # print(sdd.desc)
    # print(sdd.created_by, sdd.created_date)
    # sdd.update("OBM 인증 대응")
    # sdd.commit()
    # print(sdd.ver)
    # print(sdd.log)


