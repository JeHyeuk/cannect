from cannect.config import env
from cannect.core.ascet.amd import AmdSource, Amd
from cannect.core.subversion import SubVersion
from cannect.schema.datadictionary import DataDictionary
from cannect.utils import tools
from pandas import DataFrame
from pathlib import Path
from datetime import datetime
from typing import Union
import os, stat


SVN = SubVersion(env.SVN_PATH)
class Deliverables:
    LEN_CH_ID = 4
    LEN_IR_ID = 5
    NAME_PREV = "prev"
    NAME_POST = "post"

    def __init__(self, path: Union[Path, str]):
        self.root = Path(path)
        self.model = self.root / 'model'
        self.sdd = self.root / 'sdd'
        self.conf = self.root / 'conf'
        self.svn = self.root / 'svn'

        self.root.mkdir(parents=True, exist_ok=True)
        self.model.mkdir(parents=True, exist_ok=True)
        (self.model / self.NAME_PREV).mkdir(parents=True, exist_ok=True)
        (self.model / self.NAME_POST).mkdir(parents=True, exist_ok=True)
        self.sdd.mkdir(parents=True, exist_ok=True)
        (self.sdd / self.NAME_PREV).mkdir(parents=True, exist_ok=True)
        (self.sdd / self.NAME_POST).mkdir(parents=True, exist_ok=True)
        (self.conf / self.NAME_PREV).mkdir(parents=True, exist_ok=True)
        (self.conf / self.NAME_POST).mkdir(parents=True, exist_ok=True)
        self.svn.mkdir(parents=True, exist_ok=True)

        ppt = env.SERVER_TEMP.parent / 'src/0000_변경내역서 양식.pptx'
        self.ppt = Path(tools.copy_to(ppt, self.root))

        ir = SVN.IR / '0000_HNB_SW_IR_.xlsm'
        self.ir = Path(tools.copy_to(ir, self.root))
        return

    def __truediv__(self, other):
        return self.root.__truediv__(other)

    def get_src(self) -> DataFrame:
        data = []
        for _root, _, _files in os.walk(self.root):
            for _file in _files:
                path = Path(_root) / _file
                if self.NAME_PREV.lower() in [n.lower() for n in _root.split(os.sep)]:
                    continue

                item = DataDictionary()
                if _file.endswith('.main.amd'):
                    amd = Amd(str(path))
                    item.type = "model"
                    item.id = amd.main["OID"]
                    item.name = amd.name
                    item.path = path
                    item.obj = amd
                    item.dst = SVN.MODEL / f'ascet/trunk/{amd.main["nameSpace"]}'

                if _file.endswith('.pptx'):
                    try:
                        item.type = "report"
                        item.id = str(int(_file.split('_')[0])).zfill(self.LEN_CH_ID)
                        item.name = _file
                        item.path = path
                        item.dst = SVN.HISTORY
                    except ValueError:
                        continue

                if _file.endswith('.xlsm'):
                    try:
                        item.type = "ir"
                        item.id = str(int(_file.split('_')[0])).zfill(self.LEN_IR_ID)
                        item.name = _file
                        item.path = path
                        item.dst = SVN.IR
                    except ValueError:
                        continue

                if _file.endswith('.rtf'):
                    item.type = "sdd"
                    item.id = path.parent.name
                    item.name = _file
                    item.path = path
                    item.dst = SVN.SDD

                if _file.endswith('_confdata.xml'):
                    item.type = 'conf'
                    item.id = ''
                    item.name = _file
                    item.path = path
                    item.dst = SVN.CONF

                if _file.startswith('BF_Result_') and _file.endswith('.7z'):
                    item.type = 'ps'
                    item.id = ''
                    item.name = _file
                    item.path = path
                    item.dst = SVN.UNECE

                if item:
                    data.append(item)

        return DataFrame(data)

    def pack(self, *ignores) -> DataFrame:
        if not ignores:
            ignores = ['ir', 'report']
        else:
            ignores = [n.lower() for n in ignores]

        tools.clear(self.svn, leave_path=True)
        items = self.get_src().copy()
        drops = []
        for n in items.index:
            item = items.loc[n]
            if item.type in ignores:
                drops.append(n)
                continue

            if item.type == 'model':
                _path = self.svn / f'{item["name"]}'
                _path.mkdir(parents=True, exist_ok=True)

                tools.copy_to(item.obj.main.path, _path)
                tools.copy_to(item.obj.impl.path, _path)
                tools.copy_to(item.obj.data.path, _path)
                tools.copy_to(item.obj.spec.path, _path)

                # .scmdata.amd 가 존재하는 경우 copy
                for _root, _, _files in os.walk(self.model / self.NAME_PREV):
                    for _file in _files:
                        if _file.endswith(f'{item["name"]}.scmdata.amd'):
                            tools.copy_to(os.path.join(_root, _file), _path)
                items.loc[n, 'path'] = tools.zip(_path, outer=False)

            if item.type == 'sdd':
                _path = self.svn / f'{item["id"]}/{item["id"]}'
                _path.mkdir(parents=True, exist_ok=True)
                tools.copy_to(Path(item.path).parent, _path)
                items.loc[n, 'path'] = tools.zip(_path, outer=True)
        items = items.drop(index=drops)
        return items

    def commit(self, message:str, *ignores):
        if not ignores:
            ignores = ['ir', 'report']
        else:
            ignores = [n.lower() for n in ignores]

        items = self.pack(*ignores)
        result = ''
        for n, item in items.iterrows():
            if item.type in ignores:
                continue
            src = Path(item.path)
            dst = Path(item.dst)
            if (dst / src.name).exists():
                os.chmod(dst / src.name, stat.S_IWRITE)
                os.remove(dst / src.name)
                svn = SubVersion(tools.copy_to(src, dst))
                result += f'{svn.commit(message=message)}\n'
            else:
                svn = SubVersion(tools.copy_to(src, dst))
                svn.add()
                result += f'{svn.commit(message=message)}\n'
        return result



if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    path = r'C:\Users\Administrator\Downloads\ICE_CANFD_OBM_인증대응'
    delv = Deliverables(path)
    pack = delv.pack('ir', 'report')

    # print(pack)
    # for n, item in pack.iterrows():
    #     print(item["name"], "-"*30)
    #     print(f"src: {item['path']}")
    #     print(f"dst: {item['dst']}")
    delv.commit("[LEE.JEHYEUK] CB18734880")