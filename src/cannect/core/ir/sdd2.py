from cannect.errors import SDDError, SDDLogError, SDDNotFoundError, SDDOutOfDateError
from cannect.utils import tools
from datetime import datetime
from functools import cached_property
from pandas import DataFrame
from pathlib import Path
from striprtf.striprtf import rtf_to_text
from typing import Union
import os, re


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
        self.content = content = self.rtf2text(file)

        self._n_desc = 0
        self._iter = content.splitlines()
        return

    def _find_log_by_regex(self):
        data = []
        columns = ['ver', 'comment']
        matches = [m.strip() for m in re.findall(r'\s*\[\d+\.\d+\.\d+\]\s*', self.content)]
        for line in self:
            if self.first_line in line:
                continue
            for ver in matches:
                if ver in line:
                    data.append([
                        ver.replace("[", "").replace("]", ""),
                        line.replace(ver, "").strip()
                    ])
                    break
        return DataFrame(data=data, columns=columns).sort_values(by=columns[0], ascending=False)

    def rtf2text(self, file:Union[str, Path]):
        kwargs = {'encoding': '', 'errors':'ignore'}
        for enc in ['cp949', 'euc-kr', 'utf-8']:
            kwargs['encoding'] = enc
            with open(file, mode='r', **kwargs) as infile:
                try:
                    read = infile.read()
                    if '\\pict' in read:
                        self.has_picture = True
                        read = self.remove_pict_groups(read)
                    return rtf_to_text(read, **kwargs)
                except (UnicodeDecodeError, Exception):
                    continue
        raise UnicodeError(f'unable to decode file: {file}')

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
            return matches[0].replace("%", "").strip()
        n = first_line.find(self.ver)
        return first_line[:n].replace("[", "").replace("]", "").strip()

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
        if (self.content.count("|") > 2) and not (
            self.name.startswith('Can') or
            self.name.startswith('EpmN') or
            self.name.startswith('EpmIf')
        ):
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
                df = DataFrame(data=data, columns=columns) \
                     .sort_values(by=columns[0], ascending=False, ignore_index=True)
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

            if df.empty or (not re.findall(r'\d+\.\d+\.\d+', df.iloc[0, 0])):
                try:
                    return self._find_log_by_regex()
                except Exception:
                    raise SDDLogError(f'unable to parse sdd log')
            return df
        return self._find_log_by_regex()

    @property
    def description(self) -> str:
        n = self.content.rfind(self.ver)
        return ''

    def __iter__(self):
        for line in self._iter:
            yield line.strip()

    def __str__(self):
        return f'''name    : {self.name.rjust(len(self.ver))}
version : {self.ver}'''



if __name__ == '__main__':
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    import random
    root = r'E:\SVN\GSL_Build\7_notes-unzip'

    samples = random.sample(os.listdir(root), 10)
    for n, sample in enumerate(samples, start=1):
        _src = os.path.join(root, sample)
        print(n, _src, '-' * 50)
        try:
            sdd = SddRW(_src)
        except (FileNotFoundError, SDDNotFoundError):
            print("NOT FOUND")
            continue
        except SDDOutOfDateError:
            print("OUT OF DATE")
            continue

        print('first line:', sdd.first_line)
        print(sdd)
        print(sdd.content)
        print(sdd.log)
        break

    """
    개별 SDD 확인 용
    """
    # sdd = SddRW(r'E:\SVN\GSL_Build\7_notes-error\040g1ngg01kk1oo70c3g4sq1jom6o\040g1ngg01kk1oo70c3g4sq1jom6o')
    #
    # if not sdd.has_picture:
    #     print(sdd.content)
    # print(sdd)
    # print(f"HAS PICTURE:", sdd.has_picture)
    # print(sdd.log)
    # print("-" * 80)
    # for c in sdd.log['comment']:
    #     print(c)

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
