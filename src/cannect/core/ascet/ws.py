from cannect.core.ascet.amd import AmdIO, AmdSC
from cannect.core.subversion import Subversion
from cannect.config import env
from cannect.errors import AscetWorspaceFormatError, AmdDuplicationError, AmdNotFoundError
from pandas import DataFrame, concat
from pathlib import Path
from typing import Union
from xml.etree.ElementTree import Element, ElementTree
import os


class WorkspaceIO:

    def __init__(self, path:str=""):
        self.path = path = env.SVN_MODEL if not path else Path(path)

        if path == env.SVN_MODEL:
            fdb = env.SVN_MODEL / '.svn/wc.db'
            if not fdb.exists():
                fdb = r'\\kefico\keti\ENT\SDT\SVN\model\.svn\wc.db'
        else:
            listdir = os.listdir(path)
            if not "HNB_GASOLINE" in listdir:
                raise AscetWorspaceFormatError('NO {HNB_GASOLINE} IN WORKSPACE DIRECTORY')
            if not "HMC_ECU_Library" in listdir:
                raise AscetWorspaceFormatError('NO {HMC_ECU_Library} IN WORKSPACE DIRECTORY')

            fdb = ''
            if '.svn' in listdir:
                fdb = Path(path) / '.svn/wc.db'
            else:
                for f in listdir:
                    if f.endswith('.aws'):
                        fdb = Path(path) / f

        if not fdb:
            raise AscetWorspaceFormatError('NO .aws OR wc.db IN WORKSPACE DIRECTORY')

        if str(fdb).endswith('.db'):
            db = Subversion.read_wcdb(fdb)
            db = db[~db["local_relpath"].str.startswith("Personal")]
            self.dbtype = 'wc'
        else:
            self.dbtype = 'ws'
            db = self.parse_aws(fdb)

        self.db = db
        return

    def __getitem__(self, item):
        return self.find(item)

    def __iter__(self):
        for name, path in self.db[['name', 'local_relpath']].itertuples(index=False):
            yield name, self.path / path

    def find(self, name:str) -> str:
        if self.dbtype == 'ws':
            query = self.db[self.db['name'] == name]
            if len(query) > 1:
                duplicated = "\n".join(query['local_relpath'])
                raise AmdDuplicationError(rf'{duplicated}\nMODULE {name} DUPLICATED: SPECIFY PARENT FOLDER')
            return str(self.path / query.iloc[0]['local_relpath'])
        else:
            if not name.endswith('.zip'):
                name += '.zip'
            query = self.db[self.db['kind'] == 'file'].copy()
            query = query[query['local_relpath'].str.endswith(name)]
            if query.empty:
                raise AmdNotFoundError(f'MODULE {name} NOT FOUND')
            if len(query) > 1:
                duplicated = "\n".join(query['local_relpath'])
                raise AmdDuplicationError(rf'{duplicated}\nMODULE {name} DUPLICATED: SPECIFY PARENT FOLDER')
            return str(self.path / query.iloc[0]['local_relpath'])

    def find_bc_component(self, n:Union[str, int]):
        sep = '/' if '/' in self.db.iloc[0]['local_relpath'] else '\\'
        bc_name = [bc for bc in os.listdir(self.HNB_GASOLINE) if str(n) in bc]
        if not bc_name:
            raise FileNotFoundError(f'#{n} BC NOT EXIST')
        bc = self.db[self.db['local_relpath'].str.contains(bc_name[0])]
        bc['bc'] = bc_name[0]
        bc['file'] = bc['local_relpath'].apply(lambda x: x.split(sep)[-1])

        layers = [[] for i in range(10)]
        for _path in bc['local_relpath']:
            _layers = _path.split(sep)
            _layers = _layers[_layers.index(bc_name[0]) + 1: ]
            for i, _layer in enumerate(_layers):
                layers[i].append(_layer)

        for i, layer in enumerate(layers, start=1):
            if layer:
                bc[f'layer_{i}'] = layer


        # layers = [l for l in root.replace(path, "").split('/' if '/' in root else '\\') if l]
        # for n, layer in enumerate(layers):
        #     data[-1].update({f'layer{n + 1}': layer})
        return bc

    @property
    def HNB_GASOLINE(self) -> Path:
        db = self.db[self.db['local_relpath'].str.contains('HNB_GASOLINE')]
        if db.empty:
            return self.path / 'HNB_GASOLINE'
        return self.path / (db.iloc[0]['local_relpath'].split('HNB_GASOLINE')[0] + 'HNB_GASOLINE')

    @property
    def HMC_ECU_Library(self) -> Path:
        db = self.db[self.db['local_relpath'].str.contains('HMC_ECU_Library')]
        if db.empty:
            return self.path / 'HMC_ECU_Library'
        return self.path / (db.iloc[0]['local_relpath'].split('HMC_ECU_Library')[0] + 'HMC_ECU_Library')

    def bcPath(self, n:Union[str, int]) -> str:
        target = [path for path in os.listdir(self.HNB_GASOLINE) if str(n) in path]
        if not target:
            raise FileNotFoundError(f'#{n} BC Not Exist')
        return str(self.HNB_GASOLINE / target[0])

    def bcTree(self, n:Union[str, int]) -> DataFrame:
        r"""
        :param n:
        :return:

        출력 예시)
                                      bc                      file               layer1                        layer2        layer3                                               path
        0   _33_EnginePositionManagement               CamPosA.zip          CamPosition                     EdgeAdapt       CamPosA  D:\SVN\model\ascet\trunk\HNB_GASOLINE\_33_Engi...
        1   _33_EnginePositionManagement               CamOfsD.zip          CamPosition               OffsetDiagnosis       CamOfsD  D:\SVN\model\ascet\trunk\HNB_GASOLINE\_33_Engi...
        2   _33_EnginePositionManagement                CamSeg.zip          CamPosition                   SegmentTime        CamSeg  D:\SVN\model\ascet\trunk\HNB_GASOLINE\_33_Engi...
        ...                         ...                        ...                  ...                           ...
        29  _33_EnginePositionManagement                 EpmSv.zip       ServiceLibrary                      EpmSvLib           NaN  D:\SVN\model\ascet\trunk\HNB_GASOLINE\_33_Engi...
        30  _33_EnginePositionManagement               CamSync.zip       Syncronization                  CamPhaseSync        CamSyn  D:\SVN\model\ascet\trunk\HNB_GASOLINE\_33_Engi...
        31  _33_EnginePositionManagement                CrkSyn.zip       Syncronization             CrankPositionSync        CrkSyn  D:\SVN\model\ascet\trunk\HNB_GASOLINE\_33_Engi...
        """
        path = self.bcPath(n)
        data = []
        for root, paths, files in os.walk(path):
            for file in files:
                if not (file.endswith('.zip') or file.endswith('.main.amd')):
                    continue
                data.append({
                    'bc': os.path.basename(path),
                    'file': file,
                    'path': os.path.join(root, file),
                })
                layers = [l for l in root.replace(path, "").split('/' if '/' in root else '\\') if l]
                for n, layer in enumerate(layers):
                    data[-1].update({f'layer{n+1}': layer})
        tree = DataFrame(data)
        cols = [col for col in tree if not col == 'path'] + ['path']
        return tree[cols]

    def bcEL(self, n:Union[str, int]) -> DataFrame:
        objs = []
        tree = self.bcTree(n)
        for i, row in tree.iterrows():
            path = row['path']
            amdsc = AmdSC(path)
            amdio = AmdIO(amdsc.main)
            frame = amdio.dataframe('Element')
            # frame['bc'] = row['bc']

            objs.append(frame)
        data = concat(objs=objs, axis=0)

        unique = data[data['scope'] == 'exported']
        oids = dict(zip(unique['name'].values, unique['OID'].values))
        def __eid(_row):
            if _row.scope in ["exported"]:
                return _row.OID
            if _row["name"] in oids:
                return oids[_row["name"]]
            return None
        data["UID"] = data.apply(__eid, axis=1)
        return data

    def bcIO(self, n:Union[str, int]) -> DataFrame:
        el = self.bcEL(n).copy().set_index(keys='UID')
        el = el[["model", "name", "unit", "modelType", "basicModelType", "kind", "scope"]]
        im = el[el["scope"] == "imported"].copy()
        ex = el[el["scope"] == "exported"].copy()
        im["exportedBy"] = [ex.loc[i, "model"] if i in ex.index else "/* 외부 BC */" for i in im.index]
        return concat([im, ex], axis=0)

    def parse_aws(self, aws:Path) -> DataFrame:
        tree = ElementTree(file=aws)
        objs = []
        def _iter(tag:Element, obj:dict):
            for sub_tag in list(tag):
                parent = obj['local_relpath']
                if sub_tag.tag == 'folder':
                    obj['local_relpath'] = f"{parent}/{sub_tag.get('name')}"
                    _iter(sub_tag, obj)
                if sub_tag.tag == 'itemWithSpec':
                    obj['name'] = name = sub_tag.get('name')
                    obj['local_relpath'] = file = f"{parent}/{name}.main.amd"
                    if os.path.exists(Path(self.path) / file):
                        objs.append(obj)
                obj = {'local_relpath': parent}

        for folder in tree.findall('folder'):
            _iter(folder, {'local_relpath': folder.get('name')})

        return DataFrame(objs)

    def project_mode(self, name:str):
        name = name.split('.')[0]
        if not name in ["HNB_I3GDI", "HNB_I3MPI", "HNB_I4GDI", "HNB_I4MPI"]:
            raise KeyError(f'WRONG PROJECT NAME: {name}')

        proj = None
        for path, _, files in  (self.HNB_GASOLINE / 'Project').walk():
            for file in files:
                if file == f'{name}.main.amd':
                    proj = path / file
        if proj is None:
            raise KeyError(f'WRONG PROJECT NAME: {name}')

        amd = AmdIO(str(proj)).dataframe('Element')
        amd = amd[amd['name'] != 'dT']
        amd = amd[['name', 'componentName']].rename(columns={'componentName': 'local_relpath'})
        amd['local_relpath'] = amd['local_relpath'].apply(lambda p: f'{p[1:]}.main.amd')
        self.db = amd
        return



if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)
    from cannect import mount

    mount(r"E:\SVN")

    io = WorkspaceIO()
    # print(io.db)
    # print(io["CanHSFPCMD"])
    # print(io.bcPath(33))
    # print(io.bcTree(33))
    # print(io.bcEL(33))
    # print(io.bcIO(33))

    # io.bcIO(33).to_clipboard()

    # io = WorkspaceIO(r'D:\ETASData\ASCET6.1\Workspaces\TX4TBMTN9LDT@H30_WS54492')
    # io = WorkspaceIO()
    # print(io.db)
    # print(io["CanHSFPCMD"])
    # print(io.bcPath(33))
    # print(io.bcTree(33))
    # print(io.bcEL(33))
    # print(io.bcIO(33))
    # io.project_mode('HNB_I4GDI')
    # print(io.db)
    # print(io.find_bc_component(33))
    # for name, path in io:
    #     print(name, path)