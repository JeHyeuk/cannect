from cannect.config import env
from cannect.core.ascet import Amd
from cannect.core.ir.sdd import SddRW
from cannect.core.ir.delivereables import Deliverables
from cannect.core.ir.diff import AmdDiff
from cannect.core.subversion import SubVersion
from cannect.errors import IRFormatError, SVNError
from cannect.schema import DataDictionary
from cannect.utils import tools
from datetime import datetime
from pandas import DataFrame, ExcelWriter
from pathlib import Path
from uuid import uuid4
from typing import Union
import pandas as pd
import os


SVN = SubVersion(env.SVN_PATH)
COLUMNS = DataDictionary(
    MAIN=[
        "FunctionName", "FunctionVersion", "SCMName", "SCMRev",
        "DSMName", "DSMRev", "BSWName", "BSWRev", "SDDName", "SDDRev",
        "ChangeHistoryName", "ChangeHistoryRev", "ElementDeleted", "ElementAdded",
        "User", "Date", "Comment", "Empty", "PolyspaceName", "PolyspaceRev"
    ],
    INST=[
        "_amd", "_sdd", "_svn_SCM", "_SCMRev"
    ]
)
class IntegrationRequest(DataFrame):

    _metadata = [
        '_meta',
        '_id',
        '_path',
        'parameters'
    ]

    @classmethod
    def svn_update(cls):
        return (f'{SVN.MODEL.update()}\n'
                f'{SVN.CONF.update()}\n'
                f'{SVN.IR.update()}\n'
                f'{SVN.HISTORY.update()}\n'
                f'{SVN.UNECE.update()}')

    def __init__(self, *models, **kwargs):
        super().__init__(columns=COLUMNS.MAIN + COLUMNS.INST, dtype=str)

        self._meta = DataDictionary(
            name="",
            report="",
            title="",
            lcr="",
            cb="",
            user=kwargs.get('user', env.USERNAME),
            date=datetime.now().strftime('%Y-%m-%d'),
            comment=kwargs.get('comment', ""),
            baseline=kwargs.get('baseline', ""),
        )
        self._id = kwargs.get('id', str(uuid4()))
        self._path = Deliverables(
            Path(kwargs.get('path', env.SERVER_TEMP / f'ir')) / self._id
        )
        self._meta.name = self._path.ir.name
        self._meta.report = self._path.ppt.name
        self.parameters = []

        for model in models:
            self.add_model(model)
        return

    @property
    def meta(self):
        return self._meta

    @property
    def name(self) -> str:
        return self._meta.name

    @property
    def path(self) -> Deliverables:
        return self._path

    def add_model(self, model: Union[str, Path]):
        model = Path(model)
        if model.is_absolute() and model.suffix == '.main.amd':
            amd = Amd(str(model))
            svn = None
        else:
            if not '.' in model.name:
                model = Path(f'{model}.zip')
            svn = SVN.MODEL[str(model)]
            if isinstance(svn, list):
                raise SVNError(f'"{model}" is duplicated, specify the parent folder')
            if svn is None:
                raise SVNError(f'"{model}" not found in SVN')
            amd = Amd(str(svn))

        data = DataDictionary(_amd=amd, _svn_SCM=svn)
        data.FunctionName = name = amd.name
        data.SCMName = "\\".join(amd.main["nameSpace"][1:].split("/") + [name])

        if not name in ["DEve_Typ", "Fid_Typ", "DSig_Typ"]:
            elements = amd.main.dataframe('Element')
            if not elements.empty and not elements[
                elements['name'].str.contains('DEve') |
                elements['name'].str.contains('Fid') |
                elements['name'].str.contains('DSig')
            ].empty:
                data.DSMName = conf = f'{name.lower()}_confdata.xml'
            else:
                pass

            data.SDDName = sdd = f'{amd.main["OID"][1:]}.zip'
            SddRW(name, sdd, path=(self._path.sdd / self._path.NAME_PREV))
            data._sdd = SddRW(name, sdd, path=(self._path.sdd / self._path.NAME_POST))
            data.PolyspaceName = f"BF_Result_{name}.7z"

        self.loc[name] = data
        return

    def compare_model(self, exclude_imported: bool = False):
        prev = self._path.model / self._path.NAME_PREV
        post = self._path.model / self._path.NAME_POST
        self[['ElementAdded', 'ElementDeleted']] = self[['ElementAdded', 'ElementDeleted']].astype(str)
        for n, model in enumerate(self.index):
            prev_amd = tools.find_file(prev, f'{model}.main.amd')
            post_amd = tools.find_file(post, f'{model}.main.amd')
            if not os.path.exists(post_amd):
                continue
            if not os.path.exists(prev_amd):
                amd = Amd(post_amd).main.dataframe('Element')
                dat = Amd(post_amd).data.dataframe('DataEntry')
                self.loc[model, 'ElementAdded'] = ", ".join(amd["name"])
                params = AmdDiff.parameters2table(amd, dat)
                if not params.empty:
                    self.parameters.append(params)
                continue
            diff = AmdDiff(prev_amd, post_amd, exclude_imported=exclude_imported)
            self.loc[model, 'ElementDeleted'] = ', '.join(diff.deleted)
            self.loc[model, 'ElementAdded'] = ", ".join(diff.added)
            params = diff.added_parameters
            if not params.empty:
                self.parameters.append(params)
        return

    def is_based(self) -> bool:
        return any([val or (not pd.isna(val)) for val in self['_SCMRev']])

    def pull(self):
        df = self[COLUMNS.MAIN].copy()
        for col in df.columns:
            if col.endswith("Rev"):
                try:
                    df[col] = df[col].astype(int)
                except (ValueError, TypeError, Exception):
                    continue
        df.to_excel(
            self._path / self.name.replace(".xlsm", ".xlsx"),
            index=False
        )
        return

    def sdd_update(self, message:str=''):
        if not message:
            message = self._meta.comment
        if not message:
            raise IRFormatError('sdd comment not specified')

        self['FunctionVersion'] = self['FunctionVersion'].astype(str)
        for model in self.index:
            sdd:SddRW = self.loc[model, '_sdd']
            sdd.update(log=message)
            self.loc[model, 'FunctionVersion'] = sdd.ver
        return

    def set_base(self, *args, **kwargs):
        tools.clear(self._path.model / self._path.NAME_PREV, leave_path=True)

        self.svn_update()
        self['_SCMRev'] = self['_SCMRev'].astype(str)
        for model in self.index:
            svn = self.loc[model, '_svn_SCM']

            # SVN 정보가 없는 모델은 Base를 잡을 수 없으므로 공란 처리
            if svn is None:
                self.loc[model, '_SCMRev'] = ''
                continue

            log = svn.log()

            # Base로 설정할 target revision
            try:
                rev = abs(int(kwargs.get(model, args[0] if args else int(self.loc[model, '_SCMRev']))))
            except (ValueError, TypeError, Exception):
                raise SVNError(f'unknown revision for "{model}"')

            if str(rev) in log['revision'].values:
                target_rev = rev
            elif rev in log.index.values:
                target_rev = log.loc[rev, 'revision']
            else:
                raise SVNError(f'unknown revision for "{model}": "r{rev}"')

            svn.save_revision_as(int(target_rev), (self._path.model / self._path.NAME_PREV))
            model_path = (self._path.model / f'{self._path.NAME_PREV}/{model}.zip')
            model_path = model_path.rename(model_path.with_name(f'{model}-{target_rev}.zip'))
            tools.unzip(model_path, model_path.parent)

            self.loc[model, '_SCMRev'] = str(target_rev)
        return

    def set_attr(self, **kwargs):
        for key, value in kwargs.items():
            if not key in self._meta:
                raise AttributeError(f'unknown attribute "{key}"')
            if key.lower() == 'id':
                raise AttributeError(f'"id" is read-only attribute')
            value = value.strip()
            if key == 'name':
                value = value \
                        .replace(" ", "_") \
                        .replace("0000_HNB_SW_IR_", "") \
                        .replace(".xlsx", "") \
                        .replace(".xlsm", "")
                value = f"0000_HNB_SW_IR_{value}.xlsm"
                self._path.ir = self._path.ir.rename(self._path.ir.with_name(value))
            if key == 'report':
                value = value \
                        .replace(" ", "_") \
                        .replace("0000_", "") \
                        .replace(".pptx", "")
                value = f"0000_{value}.pptx"
                self._path.ppt = self._path.ppt.rename(self._path.ppt.with_name(value))

            if key in ['user', 'comment']:
                self[key.capitalize()] = value
            self._meta[key] = value

    def sync(self, **kwargs):
        self.svn_update()
        self[COLUMNS.MAIN] = self[COLUMNS.MAIN].astype('object')
        self['Date'] = self._meta.date
        self['User'] = self._meta.user
        self['Comment'] = self._meta.comment
        for model in self.index:
            svn = SVN.MODEL[f'{self.loc[model, "SCMName"].replace("\\", "/")}.zip']
            if svn:
                self.loc[model, 'SCMRev'] = int(svn.log().loc[0, 'revision'])

            if not pd.isna(self.loc[model, 'DSMName']):
                svn = SVN.CONF[self.loc[model, 'DSMName']]
                self.loc[model, 'DSMRev'] = int(svn.log().loc[0, 'revision'])

            if not pd.isna(self.loc[model, 'SDDName']):
                sdd = self.loc[model, '_sdd']
                if not sdd.svn is None:
                    self.loc[model, 'SDDRev'] = int(sdd.svn.log().loc[0, 'revision'])
                self.loc[model, 'FunctionVersion'] = sdd.ver

            if not pd.isna(self.loc[model, 'PolyspaceName']):
                svn = SVN.UNECE[self.loc[model, 'PolyspaceName']]
                self.loc[model, 'PolyspaceRev'] = int(svn.log().loc[0, 'revision'])


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    # print(IntegrationRequest.svn_update())
    # ir = IntegrationRequest("CanFDCCUM", "anFDCCUD", "CanFDEMSOM", "LinM/LinM",
    ir = IntegrationRequest("CatPrg/CatPrg", "CatSet", "CatFMd/CatFMd",
                            path=r'C:\Users\Administrator\Downloads\cannect-test',
                            id='ir-sdd-test',
                            comment='SDD 노트 작성 테스트')
    # ir.sdd_update()
    print(ir)
