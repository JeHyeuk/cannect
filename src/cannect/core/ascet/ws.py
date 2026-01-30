from cannect.core.ascet.amd import AmdIO, AmdSC
from cannect.core.subversion import Subversion
from cannect.config import env
from cannect.errors import AscetWorspaceFormatError, AmdDuplicationError, AmdNotFoundError
from pandas import DataFrame, concat
from pathlib import Path
from typing import Union
import os


class WorkspaceIO:

    def __init__(self, path:str=""):
        self.path = path = env.SVN_MODEL if not path else Path(path)
        if path != env.SVN_MODEL:
            listdir = os.listdir(path)
            if not "HNB_GASOLINE" in listdir:
                raise AscetWorspaceFormatError('NO {HNB_GASOLINE} IN WORKSPACE DIRECTORY')
            if not "HMC_ECU_Library" in listdir:
                raise AscetWorspaceFormatError('NO {HMC_ECU_Library} IN WORKSPACE DIRECTORY')

        if path == env.SVN_MODEL:
            fdb = r'\\kefico\keti\ENT\SDT\SVN\model\.svn\wc.db'
        else:
            fdb = ''
            if '.svn' in listdir:
                fdb = Path(path) / '.svn/wc.db'
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
            # TODO
            # .aws 파일 파싱
            pass
        self.db = db
        return

    def __getitem__(self, item):
        return self.find(item)

    def find(self, name:str) -> str:
        # TODO
        # .asw CASE 생성
        if self.dbtype == 'ws':
            pass
        else:
            if not name.endswith('.zip'):
                name += '.zip'
            query = self.db[self.db['kind'] == 'file'].copy()
            query = query[query['local_relpath'].str.endswith(name)]
            if query.empty:
                raise AmdNotFoundError(f'MODULE {name} NOT FOUND')
            if len(query) > 1:
                raise AmdDuplicationError(rf'{query}\nMODULE {name} DUPLICATED: SPECIFY PARENT FOLDER')
            return str(self.path / query.iloc[0]['local_relpath'])

    @property
    def HNB_GASOLINE(self) -> Path:
        return self.path / 'HNB_GASOLINE'

    @property
    def HMC_ECU_Library(self) -> Path:
        return self.path / 'HMC_ECU_Library'

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



if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)


    io = WorkspaceIO()
    print(io.db)
    print(io["CanHSFPCMD"])
    # print(io.bcPath(33))
    # print(io.bcTree(33))
    # print(io.bcEL(33))
    # print(io.bcIO(33))

    # io.bcIO(33).to_clipboard()