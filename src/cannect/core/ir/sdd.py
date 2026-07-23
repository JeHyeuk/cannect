from cannect.errors import (
    SDDError,
    SDDLogError,
    SDDNotFoundError,
    SDDOutOfDateError
)
from cannect.utils import tools
from datetime import datetime
from functools import cached_property
from pandas import DataFrame
from pathlib import Path
from striprtf.striprtf import rtf_to_text
from typing import Union
import os, re, string


class SddRW:

    @staticmethod
    def remove_pict_groups(text):
        """
        rtf 파일에서 사진 제거: 완벽히 동작하지 않음
        :param text:
        :return:
        """
        new = []
        for frac in text.split("\\pict"):
            if "\\bin" in frac:
                frac = frac[:frac.find("}\\par") + len("}\\par")]
            new.append(frac)
        return "".join(new)

    @staticmethod
    def encode_rtf(text: str, fallback: str = "?") -> str:
        out = []
        for ch in text:
            if ch in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] or \
                    ch in ["[", "]", ".", ",", "-", "_", ">", "<", " "] or \
                    ch.lower() in string.ascii_lowercase:
                out.append(ch)
            elif ch == '\n':
                out.append('\\par\n')
            else:
                code = ord(ch)
                code = str(code)
                out.append(f"\\u{code}{fallback}")
        return "".join(out)

    def __init__(self, file:Union[str, Path]):
        file = Path(file)

        # FunctionDefinition.rtf 파일 수배
        # 없는 경우 오류 처리
        if not str(file).endswith('.rtf'):
            try:
                file = Path(tools.find_file(file, 'FunctionDefinition.rtf'))
            except (FileNotFoundError, Exception):
                raise SDDNotFoundError(f'sdd not found error: {file}')
        if not file.exists():
            raise SDDNotFoundError(f'sdd not found error: {file}')

        # 2016년 이전 SDD 파일을 자동으로 수정하려는 경우 오류 처리
        # 형식 불일치로 수기 수정 필요
        mtime = datetime.fromtimestamp(
            os.path.getmtime(file)
        )
        if mtime.year <= 2016:
            raise SDDOutOfDateError(f'too old sdd file: "{file}" @{mtime.strftime("%Y-%m-%d")}')

        # Attributes
        self.file = file
        self.has_picture = False
        self.created_by = ''
        self.created_date = ''
        self.content = content = self.rtf2text(file)

        self._n_desc = 0
        self._iter = content.splitlines()
        return

    def _find_log_by_regex(self):
        pattern = re.compile(
            r'^\s*\[?(?P<ver>\d+\.\d+\.\d+)\]?\s*(?P<comment>.*?)(?=^\s*\[?\d+\.\d+\.\d+\]?\s*|\Z)',
            re.DOTALL | re.MULTILINE
        )

        rows = []
        for m in pattern.finditer(self.content):
            ver = m.group('ver')
            comment = m.group('comment').strip()
            rows.append([ver, comment])

        return DataFrame(rows, columns=['ver', 'comment']) \
               .sort_values(by=['ver'], ascending=False, ignore_index=True)

    def _find_log_by_table(self) -> DataFrame:
        data, columns = [], []
        flag = False
        row = ''
        for line in self:
            if flag and not line:
                break
            if "|" in line:
                flag = True
            if flag and not line.endswith("|"):
                row = line if not row else (row + f'\n{line}')
                continue
            if flag and line.endswith("|"):
                row = line if not row else (row + f'\n{line}')
                if not columns:
                    columns = row.split("|")
                    flag = True
                else:
                    data.append(row.split("|"))
                row = ''

        try:
            if len(columns) != len(set(columns)):
                seen, new = {}, []
                for x in columns:
                    if x in seen:
                        seen[x] += 1
                        new.append(f"{x}_{seen[x]}")
                    else:
                        seen[x] = 0
                        new.append(x)
                columns = new
            df = DataFrame(data=data, columns=columns)
        except (IndexError, ValueError, Exception):
            raise SDDLogError(f'unable to parse sdd log')

        if '' in df.columns:
            df.drop(columns=[''], inplace=True)
        if not all(['.' in c for c in df[df.columns[0]]]):
            df.drop(columns=[df.columns[0]], inplace=True)
        if all([not c for c in df[df.columns[-1]]]):
            df.drop(columns=[df.columns[-1]], inplace=True)
        if len(df.columns) > 2:
            df = df[[df.columns[0], df.columns[-1]]] \
                .rename(columns={df.columns[0]: 'ver', df.columns[-1]: 'comment'})
        df.sort_values(by=df.columns[0], ascending=False, ignore_index=True, inplace=True)
        if df.empty or (not re.findall(r'\d+\.\d+\.\d+', df.iloc[0, 0])):
            raise SDDLogError(f'unable to parse sdd log')
        return df

    def rtf2text(self, file:Union[str, Path]):
        kwargs = {'encoding': '', 'errors':'ignore'}
        for enc in ['cp949', 'euc-kr', 'utf-8']:
            kwargs['encoding'] = enc
            with open(file, mode='r', **kwargs) as infile:
                try:
                    read = infile.read()
                    match = re.search(r'createby.*?staticval (\d+)', read)
                    if match:
                        self.created_by = match.group(1)
                    match = re.search(r'createdate.*?staticval\s+((\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+))', read)
                    if match:
                        self.created_date = match.group(1)
                    if '\\pict' in read:
                        self.has_picture = True
                        read = self.remove_pict_groups(read)
                    return rtf_to_text(read, **kwargs)
                except (UnicodeDecodeError, Exception):
                    continue
        raise UnicodeError(f'unable to decode file: {file}')

    def write(self, user:str, dst:Union[str, Path]=''):
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logs = [
            f"\\plain\\f0\\fs20{self.encode_rtf(f'[{v}] {c}')}\\par"
            for v, c in self.log.itertuples(index=False)
        ]
        text = rf"""{{\rtf1\ansi\deff0\uc1\ansicpg949\deftab720{{\fonttbl{{\f0\fnil\fcharset1 Arial;}}{{\f1\fnil\fcharset2 Wingdings;}}{{\f2\fnil\fcharset2 Symbol;}}}}{{\colortbl\red0\green0\blue0;\red255\green0\blue0;\red0\green128\blue0;\red0\green0\blue255;\red255\green255\blue0;\red255\green0\blue255;\red128\green0\blue128;\red128\green0\blue0;\red0\green255\blue0;\red0\green255\blue255;\red0\green128\blue128;\red0\green0\blue128;\red255\green255\blue255;\red192\green192\blue192;\red128\green128\blue128;\red0\green0\blue0;}}\wpprheadfoot1\paperw11906\paperh16838\margl567\margr624\margt850\margb850\headery720\footery720\endnhere\sectdefaultcl{{\*\generator WPTools_6.250;}}{{\*\userprops {{\propname oid}}\proptype30{{\staticval 040g1j9410g01q871c90dpcrfer3k}}
{{\propname userid}}\proptype30{{\staticval {user}}}
{{\propname filename}}\proptype30{{\staticval FunctionDefinition.rtf}}
{{\propname createby}}\proptype30{{\staticval {self.created_by or user}}}
{{\propname createdate}}\proptype30{{\staticval {self.created_date or time}}}
{{\propname updateby}}\proptype30{{\staticval {user}}}
{{\propname updatedate}}\proptype30{{\staticval {time}}}
}}{{\plain\f0\fs20 %{self.name} [{self.ver}]\par
\pard\plain\plain\f0\fs20\par
\plain\f0\fs20{self.encode_rtf(self.description)}\par
{"\n".join(logs)}
}}}}"""

        with open(str(dst) or self.file, 'w') as f:
            f.write(text)
        return text

    @property
    def first_line(self) -> str:
        for line in self:
            if line:
                return line
        raise SDDError(f'sdd format error: empty sdd "{self.file}"')

    @cached_property
    def name(self) -> str:
        first_line = self.first_line
        if '%' in first_line:
            matches = re.findall(r'%\s*\S+', first_line)
            if (len(matches) > 1) or (not matches):
                raise SDDError(f'first line format error: "{first_line}"')
            name = matches[0].replace("%", "").strip()
            if '[' in name:
                name = name.split('[')[0].strip()
            return name
        return first_line.replace(self.ver, '').replace("[", "").replace("]", "").strip()

    @property
    def ver(self) -> str:
        try:
            return self.log.iloc[0, 0]
        except (KeyError, IndexError, Exception):
            matches = re.findall(r'\s*\[\d+\.\d+\.\d+\]\s*', self.first_line)
            try:
                return matches[0].strip().replace("[", "").replace("]", "")
            except (KeyError, IndexError, Exception):
                raise SDDError(f'first line format error: "{self.first_line}"')

    @property
    def log(self) -> DataFrame:
        if not hasattr(self, '_log'):
            if (self.content.count("|") > 2) and not (
                self.name.startswith('Can') or
                self.name.startswith('EpmN') or
                self.name.startswith('EpmIf')
            ):
                try:
                    self.__setattr__('_log', self._find_log_by_table())
                except SDDError:
                    self.__setattr__('_log', self._find_log_by_regex())
            else:
                self.__setattr__('_log', self._find_log_by_regex())
        return self.__getattribute__('_log')

    @log.setter
    def log(self, message:str):
        parts = self.ver.split(".")
        ver = '.'.join(parts[:-1] + [f'{int(parts[-1]) + 1}'.zfill(3)])
        log = self.log.copy()
        log.loc[len(log)] = [ver, message]
        log.sort_values(by=['ver'], inplace=True, ascending=False, ignore_index=True)
        self.__setattr__('_log', log)
        return

    @property
    def description(self) -> str:
        content = self.content[len(self.first_line) + 1:]
        for v, c in self.log.itertuples(index=False):
            content = content.replace(f'[{v}]', '').replace(v, '')
            if '\n' in c:
                for _c in c.splitlines():
                    content = content.replace(_c.strip(), '').strip()
            else:
                content = content.replace(c, '').strip()
        return '\n'.join(l for l in content.splitlines() if not '|' in l)

    def __iter__(self):
        for line in self._iter:
            yield line.strip()

    def __len__(self):
        return len(self._iter)

    def __str__(self):
        return f'''name    : {self.name.rjust(len(self.ver))}
version : {self.ver}
author  : {self.created_by}
created : {self.created_date}
picture : {self.has_picture}'''



if __name__ == '__main__':
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    # import random
    # root = r'E:\SVN\GSL_Build\7_notes-unzip'
    #
    # samples = random.sample(os.listdir(root), 10)
    # for n, sample in enumerate(samples, start=1):
    #     _src = os.path.join(root, sample)
    #     print(n, _src, '-' * 50)
    #     try:
    #         sdd = SddRW(_src)
    #     except (FileNotFoundError, SDDNotFoundError):
    #         print("NOT FOUND")
    #         continue
    #     except SDDOutOfDateError:
    #         print("OUT OF DATE")
    #         continue
    #
    #     print(sdd)
    #     print("CONTENT", "-" * 80)
    #     print(sdd.content)
    #     print("DESC", "-" * 80)
    #     print(sdd.description)
    #     print("LOG", "-" * 80)
    #     print(sdd.log.to_string(index=False, justify='left'))
    #     print("-" * 80)
    #
    #     sdd.log = "야아따 자동으로다가 SDD를 업데이트해브러~"
    #     print(sdd)
    #     print("NEW LOG", "-" * 80)
    #     print(sdd.log.astype(str).to_string(index=False, justify='left'))
    #     break

    """
    개별 SDD 확인 용
    """
    sdd = SddRW(r'C:\Users\Administrator\Downloads\cannect-test\hello world\sdd\변경 전\040g00002u801po71g9g7ti67io00')
    print(sdd)
    print(f"HAS PICTURE:", sdd.has_picture)
    print("CONTENT", "-" * 80)
    print(sdd.content)
    print("DESC", "-" * 80)
    print(sdd.description)
    print("LOG", "-" * 80)
    print(sdd.log)
    print("-" * 80)
    for v, c in sdd.log.itertuples(index=False):
        print(f'-> {v}: {c}')

    """
    전체 SDD에서 오류 항목 찾기
    """
    # from tqdm.auto import tqdm
    #
    # loop = tqdm(os.listdir(root))
    # for oid in loop:
    #     if oid in ['040g030000001mo710eg5p6icjpja']:
    #         continue
    #     _src = os.path.join(root, oid)
    #     try:
    #         sdd = SddRW(_src)
    #     except (SDDNotFoundError, SDDOutOfDateError):
    #         continue
    #
    #     try:
    #         loop.set_description(f'{oid}: {sdd.name}')
    #         temp = f'{sdd} {sdd.log}'
    #     except (SDDError, SDDLogError):
    #         tools.unzip(
    #             Path(r'E:\SVN\GSL_Build\7_Notes') / f'{oid}.zip',
    #             Path(r'E:\SVN\GSL_Build\7_notes-error') / oid
    #         )
