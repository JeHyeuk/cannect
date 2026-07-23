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
    NAME_PREV = "변경 전"
    NAME_POST = "변경 후"

    def __init__(self, path: Union[Path, str]):
        self.root = Path(path)
        self.model = self.root / 'model'
        self.sdd = self.root / 'sdd'
        self.conf = self.root / 'conf'

        self.root.mkdir(parents=True, exist_ok=True)
        self.model.mkdir(parents=True, exist_ok=True)
        (self.model / self.NAME_PREV).mkdir(parents=True, exist_ok=True)
        (self.model / self.NAME_POST).mkdir(parents=True, exist_ok=True)
        self.sdd.mkdir(parents=True, exist_ok=True)
        (self.sdd / self.NAME_PREV).mkdir(parents=True, exist_ok=True)
        (self.sdd / self.NAME_POST).mkdir(parents=True, exist_ok=True)
        (self.conf / self.NAME_PREV).mkdir(parents=True, exist_ok=True)
        (self.conf / self.NAME_POST).mkdir(parents=True, exist_ok=True)

        ppt = env.SERVER_TEMP.parent / 'src/0000_변경내역서 양식.pptx'
        self.ppt = Path(tools.copy_to(ppt, self.root))

        ir = SVN.IR / '0000_HNB_SW_IR_.xlsm'
        self.ir = Path(tools.copy_to(ir, self.root))
        return

    def __repr__(self):
        return repr(self.get_src())

    def __str__(self):
        return str(self.get_src())

    def __truediv__(self, other):
        return self.root.__truediv__(other)

    def get_src(self) -> DataFrame:
        """
        경로 내 위치한 통합 요청 리소스 파일을 모두 수집(확장자 기준)
        * 변경 전/후 구분 없이 모두 수집하며 마지막 수정(생성)일자를 포함.
        :return:
        """
        data = []
        for _root, _, _files in os.walk(self.root):
            for _file in _files:

                if _file.endswith('.main.amd'):
                    amd = Amd(str(path))
                    for _amd in amd:
                        path = Path(_amd.path)
                        date = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        data.append(dict(
                            type='model',
                            name=amd.name,
                            file=_amd.name,
                            date=date,
                            src=path,
                            dst=SVN.MODEL / f'ascet/trunk/{amd.main["nameSpace"]}'
                        ))
                    continue

                path = Path(_root) / _file
                date = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                item = DataDictionary(name=path.name, file=_file, date=date, src=path)
                if _file.endswith('.pptx'):
                    item.type = 'report'
                    item.dst = SVN.HISTORY

                if _file.endswith('.xlsm'):
                    item.type = 'ir'
                    item.dst = SVN.IR

                if _file.endswith('.rtf'):
                    item.type = "sdd"
                    item.name = path.parent.name
                    item.dst = SVN.SDD

                if _file.endswith('_confdata.xml'):
                    item.type = 'conf'
                    item.dst = SVN.CONF

                if _file.startswith('BF_Result_') and _file.endswith('.7z'):
                    item.type = 'ps'
                    item.dst = SVN.UNECE

                data.append(item)

        return DataFrame(data)

    def commit_resource(self) -> DataFrame:
        svn = self.root / '__temp__'
        svn.mkdir(parents=True, exist_ok=True)
        tools.clear(svn, leave_path=True)

        items = self.get_src().copy()
        items['id'] = items['name'] + items['file']
        items['od'] = items['date'].astype(str) \
                      .str.replace('-', '') \
                      .str.replace(' ', '') \
                      .str.replace(':', '') \
                      .astype(int)

        items = items.sort_values('od', ascending=False).drop_duplicates(subset='id', keep='first')
        sdd = items[items['type'] == 'sdd']
        print(sdd)


        # drops = []
        # for n in items.index:
        #     item = items.loc[n]
        #     if item.type in ignores:
        #         drops.append(n)
        #         continue
        #
        #     if item.type == 'model':
        #         _path = self.svn / f'{item["name"]}'
        #         _path.mkdir(parents=True, exist_ok=True)
        #
        #         tools.copy_to(item.obj.main.path, _path)
        #         tools.copy_to(item.obj.impl.path, _path)
        #         tools.copy_to(item.obj.data.path, _path)
        #         tools.copy_to(item.obj.spec.path, _path)
        #
        #         # .scmdata.amd 가 존재하는 경우 copy
        #         for _root, _, _files in os.walk(self.model / self.NAME_PREV):
        #             for _file in _files:
        #                 if _file.endswith(f'{item["name"]}.scmdata.amd'):
        #                     tools.copy_to(os.path.join(_root, _file), _path)
        #         items.loc[n, 'path'] = tools.zip(_path, outer=False)
        #
        #     if item.type == 'sdd':
        #         _path = self.svn / f'{item["id"]}/{item["id"]}'
        #         _path.mkdir(parents=True, exist_ok=True)
        #         tools.copy_to(Path(item.path).parent, _path)
        #         items.loc[n, 'path'] = tools.zip(_path, outer=True)
        # items = items.drop(index=drops)
        # return items

    # def pack(self, *ignores) -> DataFrame:
    #     if not ignores:
    #         ignores = ['ir', 'report']
    #     else:
    #         ignores = [n.lower() for n in ignores]
    #
    #     tools.clear(self.svn, leave_path=True)
    #     items = self.get_src().copy()
    #     drops = []
    #     for n in items.index:
    #         item = items.loc[n]
    #         if item.type in ignores:
    #             drops.append(n)
    #             continue
    #
    #         if item.type == 'model':
    #             _path = self.svn / f'{item["name"]}'
    #             _path.mkdir(parents=True, exist_ok=True)
    #
    #             tools.copy_to(item.obj.main.path, _path)
    #             tools.copy_to(item.obj.impl.path, _path)
    #             tools.copy_to(item.obj.data.path, _path)
    #             tools.copy_to(item.obj.spec.path, _path)
    #
    #             # .scmdata.amd 가 존재하는 경우 copy
    #             for _root, _, _files in os.walk(self.model / self.NAME_PREV):
    #                 for _file in _files:
    #                     if _file.endswith(f'{item["name"]}.scmdata.amd'):
    #                         tools.copy_to(os.path.join(_root, _file), _path)
    #             items.loc[n, 'path'] = tools.zip(_path, outer=False)
    #
    #         if item.type == 'sdd':
    #             _path = self.svn / f'{item["id"]}/{item["id"]}'
    #             _path.mkdir(parents=True, exist_ok=True)
    #             tools.copy_to(Path(item.path).parent, _path)
    #             items.loc[n, 'path'] = tools.zip(_path, outer=True)
    #     items = items.drop(index=drops)
    #     return items

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

    path = r'C:\Users\Administrator\Downloads\hello world'
    output = Deliverables(path)
    output.commit_resource()

    # print(pack)
    # for n, item in pack.iterrows():
    #     print(item["name"], "-"*30)
    #     print(f"src: {item['path']}")
    #     print(f"dst: {item['dst']}")
    # delv.commit("[LEE.JEHYEUK] CB18734880")