from datetime import datetime
from typing import Any, SupportsBytes, Union
import os, string


class SddRW:

    @classmethod
    def _to_rtf(cls, text: str, fallback: str = "?") -> str:
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
    def generate(
            cls,
            path:str,
            name:str,
            oid:str,
            description:str,
            log:str='최초 배포'
    ):
        """
        @path: SDD 노트 생성 상위 경로
        @name: 모델 이름
        @oid : 모델 OID
        @description : 모델 기능 Description
        @log : 최초 로그
        """
        root = os.path.join(path, oid)
        os.makedirs(root, exist_ok=True)
        time = datetime.now().strftime('%Y%m%d %H%M%S')
        with open(os.path.join(root, 'FunctionDefinition.rtf'), 'w', encoding="ansi") as f:
            f.write(r"""{\rtf1\ansi\deff0\uc1\ansicpg949\deftab720{\fonttbl{\f0\fnil\fcharset1 Arial;}{\f1\fnil\fcharset2 Wingdings;}{\f2\fnil\fcharset2 Symbol;}}{\colortbl\red0\green0\blue0;\red255\green0\blue0;\red0\green128\blue0;\red0\green0\blue255;\red255\green255\blue0;\red255\green0\blue255;\red128\green0\blue128;\red128\green0\blue0;\red0\green255\blue0;\red0\green255\blue255;\red0\green128\blue128;\red0\green0\blue128;\red255\green255\blue255;\red192\green192\blue192;\red128\green128\blue128;\red0\green0\blue0;}\wpprheadfoot1\paperw11906\paperh16838\margl567\margr624\margt850\margb850\headery720\footery720\endnhere\sectdefaultcl{\*\generator WPTools_6.250;}{\*\userprops {\propname oid}\proptype30{\staticval 040g1j9410g01q871c90dpcrfer3k}
{\propname userid}\proptype30{\staticval user}
{\propname filename}\proptype30{\staticval FunctionDefinition.rtf}
{\propname createby}\proptype30{\staticval user}
{\propname createdate}\proptype30{\staticval time}
{\propname updateby}\proptype30{\staticval user}
{\propname updatedate}\proptype30{\staticval time}
}{\plain\f0\fs20 %__NAME__ [00.00.001]\par
\pard\plain\plain\f0\fs20\par
\plain\f0\fs20 __DESCRIPTION__\par
\pard\plain\plain\f0\fs20\par
\plain\f0\fs20\u9654 ?\u48320 ?\u44221 ?\u45236 ?\u50669 ?\par
\plain\f0\fs20 [00.00.001] __LOG__\par
}}""" \
        .replace("user", os.environ.get("USERNAME", "UNKNOWN")) \
        .replace("time", time) \
        .replace("__NAME__", name) \
        .replace("__DESCRIPTION__", cls._to_rtf(description)) \
        .replace("__LOG__", cls._to_rtf(log))
            )
        return

    def __init__(self, sdd:Union[Any, str, SupportsBytes]):
        self.fullpath = ''
        if sdd.endswith('.rtf'):
            self.fullpath = sdd
        else:
            for path, _, files in os.walk(sdd):
                for file in files:
                    if not file == "FunctionDefinition.rtf":
                        continue
                    self.fullpath = os.path.join(path, file)
        if not self.fullpath:
            raise FileExistsError(f'{sdd} NOT FOUND')

        self.version_doc = ''
        self._n_doc = -1
        self.version_log = ''
        self.font = r'\f1'

        self.syntax = []
        with open(self.fullpath, "r", encoding='ansi') as f:
            for n, line in enumerate(f.readlines()):
                if "Arial" in line:
                    clip = line[:line.find('Arial')]
                    self.font = clip[clip.rfind('{') + 1:][:3]
                if not self.version_doc and "[" in line and "]" in line:
                    if r"\f1" in line:
                        line = line.replace(r"\f1", "")
                    self.version_doc = line[line.find('[') + 1:line.find(']')].replace(" ", "")
                    self._n_doc = n

                if self.version_doc and not self.version_log and "[" in line and "]" in line:
                    if r"\f1" in line:
                        line = line.replace(r"\f1", "")
                    self.version_log = line[line.find('[') + 1:line.find(']')].replace(" ", "")

                self.syntax.append(line)
        return

    def update(self, log:str):

        if self._n_doc == -1:
            return "FAILED TO UPDATE SDD"
        split = self.version_doc.split(".")
        split[-1] = str(int(split[-1]) + 1).zfill(3)
        self.version_doc = ".".join(split)

        doc = self.syntax[self._n_doc]
        prefix = doc[:doc.find('[') + 1]
        suffix = doc[doc.find(']'): ]
        self.syntax[self._n_doc] = f'{prefix}{self.version_doc}{suffix}'

        log = self._to_rtf(log)
        syntax = []
        for line in self.syntax:
            if self.version_log in line:
                syntax.append(rf'\wpparid0\plain{self.font}\fs20 [{self.version_doc}] {log} \par' + '\n')
            syntax.append(line)

        self.version_log = self.version_doc
        with open(self.fullpath, "w", encoding="ansi") as f:
            f.write("".join(syntax))
        return ''


if __name__ == "__main__":

    sdd = SddReader(
        r'D:\SDD\Notes\Files\040g030000001oo7086g4s4088ajq\FunctionDefinition.rtf'
        # r"D:\Archive\00_프로젝트\2017 통신개발-\2026\DS0114 CR10785688 CNGPIO HS\05_Resources\SDD\040g030000001mo710eg5tbsm1ejc"
        # r"C:\Users\ADMINI~1\AppData\Local\Temp\~cannect\040g030000001oo7086g4s4088ajq"
    )
    print(sdd.version_doc)
    status = sdd.update('testing')
    print(sdd.version_doc)


    # SddReader.generate(
    #     path=r'D:\SDD\Notes\Files',
    #     name='CanFDEMS06',
    #     oid='040g030000001oo7086g4s4088ajq',
    #     description='EMS_06_100ms 메시지 송신\n(* SDD NOTE MS WORD 수정 금지)',
    #     log='최초 배포'
    # )