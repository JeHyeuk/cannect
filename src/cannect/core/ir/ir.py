from cannect.config import env
from cannect.core.ascet import Amd
from cannect.core.ir.diff import AmdDiff
from cannect.core.ir.sdd import SddRW
from cannect.core.ir.sourcecontrol import SourceControl, Compare
from cannect.core.subversion import SubVersion
from cannect.errors import (
    IRFormatError,
    SDDError,
    SVNError
)
from cannect.schema import DataDictionary
from cannect.utils import tools, ComExcel, PptRW

from datetime import datetime
from dataclasses import dataclass
from pandas import DataFrame
from pathlib import Path
from uuid import uuid4
from typing import Union
import os, stat, time


SVN = SubVersion(env.SVN_PATH)
class IntegrationRequest:

    @dataclass
    class __meta__:
        baseline: str=''
        cb      : Union[int, str]=''
        comment : str=''
        date    : str= datetime.now().strftime("%Y-%m-%d")
        lcr     : str=''
        name    : str=''
        report  : str=''
        title   : str=''
        user_kor: str=''
        user_eng: str=''

    COLUMNS = [
        "FunctionName", "FunctionVersion",
        "SCMName", "SCMRev",
        "DSMName", "DSMRev",
        "BSWName", "BSWRev",
        "SDDName", "SDDRev",
        "ChangeHistoryName", "ChangeHistoryRev",
        "ElementDeleted", "ElementAdded",
        "User", "Date", "Comment", " ",
        "PolyspaceName", "PolyspaceRev"
    ]

    def __init__(self, *model, **kwargs):
        root = Path(kwargs.get('path', env.SERVER_TEMP / f"{kwargs.get('id', env.USERNAME)}/ir"))

        self.sc = SourceControl(root / kwargs.get('name', str(uuid4())))
        self.sc.update()

        self.data = DataFrame(columns=self.COLUMNS)
        self.inst = DataDictionary()
        self.meta = self.__meta__()
        for meta in self.meta.__dict__:
            if meta in kwargs:
                self.meta.__dict__[meta] = kwargs[meta]

        for md in model:
            self.append(md)
        return

    def __call__(self) -> DataFrame:
        self.finalize()
        return self.data

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return str(self())

    def __repr__(self):
        return repr(self())

    def append(self, model: Union[str, Path]):
        model = Path(model)
        if model.is_absolute() and model.suffix == '.main.amd':
            # 절대 경로로 모델(*.main.amd)를 직접 입력하는 경우
            amd = Amd(str(model))
            svn = SVN.MODEL[f'{"/".join(amd.main["nameSpace"].split("/")[-2:])}/{amd.name}.zip']
        else:
            # 모델 이름만 입력하는 경우: SVN에서 정보 취득
            svn = SVN.MODEL[f'{model}.zip' if not model.name.endswith('.zip') else model.name]
            if isinstance(svn, list):
                raise SVNError(f'"{model}" is duplicated, specify the parent folder')
            if svn is None:
                raise SVNError(f'"{model}" not found in SVN')
            amd = Amd(str(svn))

        name = amd.name
        self.sc.svn[name] = DataDictionary(model={'src': svn, 'rev': None})
        self.inst[name] = DataDictionary(amd=amd)
        if (self.sc.dst.sdd.post / (amd.main['OID'][1:])).exists():
            self.inst[name].sdd = SddRW(self.sc.dst.sdd.post / (amd.main['OID'][1:]))
        self.data.loc[name] = {c: '' for c in self.COLUMNS}
        self.data.loc[name, "FunctionName"] = name
        self.data.loc[name, "SCMName"] = ns =  "\\".join(amd.main["nameSpace"][1:].split("/") + [name])
        if "HMC_DiagLibrary\\DSM_Types" in ns:
            return

        elem = amd.main.dataframe('Element')
        try:
            elem = elem[elem['componentName'].str.contains("HMC_DiagLibrary/DSM_Types")]
            if not elem.empty:
                self.data.loc[name, "DSMName"] = conf = f'{name.lower()}_confdata.xml'
                self.sc.svn[name].conf = {'src': SVN.CONF[conf], 'rev': None}
        except (IndexError, KeyError):
            pass

        self.data.loc[name, "SDDName"] = sdd = f'{amd.main["OID"][1:]}.zip'
        self.sc.svn[name].sdd = {'src': SVN.SDD[sdd], 'rev': None}

        self.data.loc[name, "PolyspaceName"] = ps = f"BF_Result_{name}.7z"
        self.sc.svn[name].ps = {'src': SVN.UNECE[ps], 'rev': None}
        return

    def base(self, *args, **kwargs):
        self.sc.update()
        for path in self.sc.dst.values():
            if isinstance(path, DataDictionary) and 'prev' in path:
                tools.clear(path.prev, leave_path=True)

        for md in self.data.index:
            svn = self.sc.svn[md]

            if 'conf' in svn:
                try:
                    log = svn.conf.src.log()
                    svn.conf.rev = log.loc[0, 'revision']

                    mtime = datetime.strptime(log.loc[0, 'date'], "%Y-%m-%d %H:%M:%S")
                    svn.conf.date = int(mtime.strftime("%Y%m%d%H%M%S"))
                    os.utime(tools.copy_to(svn.conf.src, self.sc.dst.conf.prev), (mtime.timestamp(), mtime.timestamp()))
                except (IndexError, Exception):
                    svn.conf.rev = None
                    svn.conf.date = None

            oid = self.inst[md].amd.main['OID'][1:]
            if 'sdd' in svn:
                try:
                    log = svn.sdd.src.log()
                    svn.sdd.rev = log.loc[0, 'revision']

                    mtime = datetime.strptime(log.loc[0, 'date'], "%Y-%m-%d %H:%M:%S")
                    svn.sdd.date = int(mtime.strftime("%Y%m%d%H%M%S"))
                    sdd = tools.unzip(svn.sdd.src, self.sc.dst.sdd.prev / oid)

                    os.utime(sdd, (mtime.timestamp(), mtime.timestamp()))
                    os.utime(sdd / oid, (mtime.timestamp(), mtime.timestamp()))
                    for rtf in os.listdir(sdd / oid):
                        os.utime(sdd / oid / rtf, (mtime.timestamp(), mtime.timestamp()))
                    tools.unzip(svn.sdd.src, self.sc.dst.sdd.post / oid)
                except (IndexError, Exception):
                    svn.sdd.rev = None
                    svn.sdd.date = None

            else:
                dst = self.sc.dst.sdd.post / oid
                dst.mkdir(parents=True, exist_ok=True)
                tools.copy_to(env.SERVER_TEMP.parent / 'src/FunctionDefinition.rtf', dst)
                with open(str(dst / 'FunctionDefinition.rtf'), 'r') as f:
                    content = f.read()
                with open(str(dst / 'FunctionDefinition.rtf'), 'w') as f:
                    f.write(content.replace("__NAME__", md))

            try:
                self.inst[md].sdd = SddRW(self.sc.dst.sdd.post / oid)
            except (SDDError, Exception):
                self.inst[md].sdd = None

            try:
                log = svn.model.src.log()
                rev = str(kwargs.get(md, args[0] if args else 0 if svn.model.rev is None else svn.model.rev))
                if rev in log['revision'].values:
                    svn.model.rev = rev
                elif int(rev) in log.index.values:
                    svn.model.rev = rev = log.loc[int(rev), 'revision']
                else:
                    raise Exception()
                rev_n = log['revision'].tolist().index(rev)
            except (IndexError, KeyError, Exception):
                raise SVNError(f'error while get base: unknwon revision for "{md}"')

            mtime = datetime.strptime(log.loc[rev_n, 'date'], "%Y-%m-%d %H:%M:%S")
            svn.model.date = int(mtime.strftime("%Y%m%d%H%M%S"))
            svn.model.src.save_revision_as(int(rev), self.sc.dst.model.prev)
            path = self.sc.dst.model.prev / f'{md}.zip'
            path = path.rename(path.with_name(f'{md}-{rev}.zip'))
            path_md = tools.unzip(path, path.parent / f'{md}-{rev}')

            os.utime(path, (mtime.timestamp(), mtime.timestamp()))
            os.utime(path_md, (mtime.timestamp(), mtime.timestamp()))
            for amd in os.listdir(path_md):
                os.utime(path_md / amd, (mtime.timestamp(), mtime.timestamp()))
        return

    def commit(self, log:str='', exceptions:list=None) -> str:
        """
        통합요청 산출물을 SVN에 Commit 한다.

        :param log:
        :param exceptions:
        :return:
        """
        def _interface(s:Path, f:Path, l:str) -> str:
            try:
                if Compare(s, f):
                    return f'skipped for commit: {f.name} is not modified'
            except FileNotFoundError:
                pass

            if f.exists():
                os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
                f.unlink()

            f = SubVersion(tools.copy_to(s, f.parent))
            if not f.is_version_controlled():
                f.add()
            return f.commit(l)

        if not log:
            log = f'[{self.meta.user_eng}] CB{self.meta.cb}'
        if exceptions is None:
            exceptions = []

        self.sc.update()

        info = ''
        src = self.sc.pack(self.data)
        for md in self.data.index:
            for key, col in [
                ('model', "FunctionName"),
                ('conf', "DSMName"),
                ('sdd', "SDDName"),
                ('ps', "PolyspaceName")
            ]:

                if key in exceptions:
                    # 사용자가 commit을 원하지 않는 항목은 제외
                    continue
                filename = self.data.loc[md, col]
                if key == 'model':
                    filename = f'{filename}.zip'
                _src = src[src['name'] == filename]
                if (not filename) or _src.empty:
                    continue

                if len(_src) > 1:
                    raise IRFormatError(f'"{md}" -> {col} is duplicated\n{_src.to_string(index=False)}')
                commit_log = log
                if key == 'ps':
                    if not self.data.loc[md, "SCMRev"]:
                        self.sync()
                    commit_log = (f'Module : {md}\n'
                                  f'Revision : {self.data.loc[md, "SCMRev"]}\n'
                                  f'Version : {self.data.loc[md, "FunctionVersion"]}\n'
                                  f'Baseline : {self.meta.baseline}\n'
                                  f'Tester : {self.meta.user_eng}')

                _src = _src.iloc[0]
                if _src['svn'].is_file():
                    svn = _src['svn']
                else:
                    svn = _src['svn'] / _src['name']
                info += _interface(_src['path'], svn, commit_log)
                self.data.loc[md, col.replace("Name", "Rev")] = SubVersion(svn).log().iloc[0, 0]

        if not 'ppt' in exceptions:
            # 변경내역서 Revision을 최신화 한다.
            com = PptRW(self.sc.src.ppt.src)
            replace = []
            for md in self.data.index:
                for slide in com.get_slide_n(f'{md} '):
                    p_rev = com.get_table_text(slide, 1, (1, 2)).split('.')[-1].replace(")", "")
                    com.replace_text_in_table(
                        n_slide=slide,
                        n_table=1,
                        cell=(1, 2),
                        prev=p_rev,
                        post=self.data.loc[md, "SCMRev"],
                    )
                replace.append((f"{{--{md}--}}", self.data.loc[md, "SCMRev"]))

            slide1_text = com.get_table_text(2, 1, (2, 2))
            for p, c in replace:
                slide1_text = slide1_text.replace(p, c)
            com.set_text_in_table(2, 1, (2, 2), slide1_text)

            time.sleep(1)
            com.close()

            inv = SVN.HISTORY.inventory
            inv = inv[inv['kind'] == 'file'].sort_values(by=['date'], ascending=False)
            new =  "_".join(
                [str(int(inv.iloc[0, 0].split("_")[0]) + 1)] + self.sc.src.ppt.src.name.split('_')[1:]
            )
            self.sc.src.ppt.src = self.sc.src.ppt.src.rename(self.sc.src.ppt.src.with_name(new))
            info += _interface(
                self.sc.src.ppt.src,
                SVN.HISTORY / self.sc.src.ppt.src.name,
                log
            )
            ppt = SubVersion(SVN.HISTORY / self.sc.src.ppt.src.name)
            self.data['ChangeHistoryName'] = ppt.name
            self.data['ChangeHistoryRev'] = ppt.log().iloc[0, 0]

        if not 'ir' in exceptions:
            self.sync()
            self.write()
            # TODO
            # 최종 IR 문서 산출물 Commit
        return info

    def finalize(self, compare:bool=True):
        self.data['User'] = self.meta.user_kor
        self.data['Date'] = self.meta.date
        self.data['Comment'] = self.meta.comment

        if compare:
            for md in self.data.index:
                prev = None
                for file in os.listdir(self.sc.dst.model.prev):
                    if file.startswith(md) and file.endswith('.zip'):
                        prev = self.sc.dst.model.prev / file

                try:
                    post = None
                    for file in os.listdir(self.sc.dst.model.post):
                        if file.startswith(md) and file.endswith('.zip'):
                            post = self.sc.dst.model.post / file
                    if post is None:
                        post = tools.find_file(self.sc.dst.model.post, f'{md}.main.amd')
                except (FileNotFoundError, Exception):
                    continue

                if prev is None:
                    post = Amd(post)
                    elem = post.main.dataframe('Element')
                    data = post.data.dataframe('DataEntry')
                    self.data.loc[md, 'ElementAdded'] = ", ".join(elem['name'])
                    param = AmdDiff.parameters2table(elem, data)
                    if not param.empty:
                        self.inst[md].param = param
                    continue

                diff = AmdDiff(prev, post, exclude_imported=False)
                self.data.loc[md, 'ElementDeleted'] = ', '.join(diff.deleted)
                self.data.loc[md, 'ElementAdded'] = ", ".join(diff.added)
                params = diff.added_parameters
                if not params.empty:
                    self.inst[md].param = params
        return

    def sdd_update(self, message:str=''):
        if not message:
            message = self.meta.comment
        if not message:
            raise IRFormatError('sdd comment not specified')

        for md in self.data.index:
            sdd:SddRW = self.inst[md].sdd
            sdd.log = message
            sdd.write(user=self.meta.user_eng or 'cannect')
            self.data.loc[md, 'FunctionVersion'] = sdd.ver
        return

    def sync(self):
        match = {
            'conf': 'DSMRev',
            'model': 'SCMRev',
            'ps':'PolyspaceRev',
            'sdd': 'SDDRev',
        }
        self.sc.update()
        for md in self.data.index:
            for item, svn in self.sc.svn[md].items():
                key = match[item]
                try:
                    self.data.loc[md, key] = svn.src.log().iloc[0, 0]
                except (IndexError, Exception):
                    continue
            sdd = self.inst[md].sdd
            try:
                self.data.loc[md, 'FunctionVersion'] = sdd.ver
            except (AttributeError, Exception):
                continue
        return

    def write(self):
        ir = self()
        xl = ComExcel(self.sc.src.ir.src, visible=True) # visible=True 는 임시, 실사용에선 삭제
        ws = xl[2]
        ws.Range(f"A3:T{3 + len(ir) - 1}").Value = ir.values.tolist()
        xl.wb.Save()
        xl.close()
        if not xl.was_open:
            xl.app.Quit()
        return


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    from cannect.core.codebeamer import cb_tester
    import asyncio

    cb = asyncio.run(cb_tester(21021985))
    name, flag = '', False
    for char in cb.summary:
        if char == '[':
            flag = True
        if flag and char == ']':
            flag = False
        if not flag and (char != ']'):
            name += "_" if char in ['/'] else char
    name = name.replace("___", "_").replace("__", "_").strip()
    # print(name)

    ir = IntegrationRequest(
        *cb.models,
        baseline=cb.baseline,
        cb=cb.item,
        comment=f"CB{cb.item} {cb.summary}",
        id='22011148',
        lcr=cb.lcr_number,
        name=name,
        title=cb.summary,
        user_kor="이제혁",
        user_eng="LEE JEHYEUK"

        # "LinM/LinM", "LinD", "ComDef",
        # "CanFDEMSM14",
        # id="EMS_IsgWarning 신호 조건 중 자동변속기에 CVT 추가",
        # name="Hello World",
        # cb='98765421',
        # comment='hello world'
    )
    # print(ir)
    # ir.meta.user = env.USERNAME
    # ir.base(1)
    # ir.sdd_update()
    # ir.sync()
    # print(ir.commit())
    print(ir.commit(exceptions=['conf', 'ir', 'model', 'sdd']))
    # ir.write()

    # print(ir.meta)
    # print(ir.sc.dst)
    # print(ir.sc.src)
    # print(ir.sc.svn)
    # print(ir.inst)
    # print(ir)
