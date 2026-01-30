from cannect.config import env
from cannect.core.ascet.amd import Amd
from cannect.core.ascet.ws import WorkspaceIO
from cannect.core.can.ascet import _db2code, _db2elem
from cannect.core.can.db.reader import CANDBReader
from cannect.schema.datadictionary import DataDictionary
from cannect.utils.logger import Logger
from cannect.utils import tools

from typing import Any, Union, Tuple
from pandas import DataFrame
import os, copy


class ComDef:

    def __init__(
        self,
        db:CANDBReader,
        engine_spec:str,
        base_model:str='',
        exclude_tsw:bool=True,
    ):
        exclude_ecus = ["EMS", "CVVD", "MHSG", "NOx"]
        if engine_spec == "ICE":
            exclude_ecus += ["BMS", "LDC"]
        db = db[~db["ECU"].isin(exclude_ecus)]
        if not db.is_developer_mode():
            db = db.to_developer_mode(engine_spec)

        if base_model:
            name = os.path.basename(base_model).split(".")[0]
        else:
            name = f"ComDef{'_HEV' if engine_spec == 'HEV' else ''}"
            base_model = WorkspaceIO()[name]

        # 공용 속성 생성
        self.db = db
        self.name = name
        self.engine_spec = engine_spec

        # 각 amd의 IO 생성
        amd = Amd(base_model)
        self.main = amd.main
        self.impl = amd.impl
        self.data = amd.data
        self.spec = amd.spec

        (env.DOWNLOADS / name).mkdir(exist_ok=True, parents=True)
        self.logger = logger = Logger(env.DOWNLOADS / rf'{name}/log.txt', clean_record=True)
        logger.info(f"%{name} MODEL GENERATION")
        logger.info(f">>> Engine Spec : {engine_spec}")
        logger.info(f">>> Base Model  : {tools.path_abbreviate(base_model)}")
        logger.info(f">>> DB Revision : {db.revision}")
        logger.info(f">>> Exclude TSW : {'Yes' if exclude_tsw else 'No'}")

        """
        변경 전 모델 요소 수집
        """
        logger.info(">>> Collecting Base Model Properties... 0.01s")
        prev = self.collect_properties()
        oids = dict(zip(prev.Elements['name'], prev.Elements.index))
        oids.update(dict(zip(prev.MethodSignature['name'], prev.MethodSignature.index)))
        self.prev = prev
        self.oids = oids

        """
        DB 메시지 기반의 요소 생성
        """
        logger.run()
        self.ME = {name: _db2elem.MessageElement(obj, oid_tag=oids) for name, obj in db.messages.items()}
        self.MC = {name: _db2code.MessageCode(obj, exclude_tsw) for name, obj in db.messages.items()}
        logger.end(">>> Defining Message Elements...")

        logger.run()
        self.SE = [_db2elem.SignalElement(sig, oid_tag=oids) for sig in db.signals.values()]
        logger.end(">>> Defining Signal Elements...")
        return

    def autorun(self):
        self.main.find('Component/Comment').text = _db2code.INFO(self.db.revision)
        self.define_elements('MethodSignature')
        self.define_elements('Element')
        self.define_elements('ImplementationEntry')
        self.define_elements('DataEntry')
        self.define_elements('HeaderBlock')
        self.define_elements('MethodBody')
        self.export()

        curr = self.collect_properties()
        deleted = list(set(self.prev.Elements['name']) - set(curr.Elements['name']))
        added = list(set(curr.Elements['name']) - set(self.prev.Elements['name']))
        desc = DataFrame(
            data={
                ("Method", "Total"): [len(self.prev.MethodSignature), len(self.db.messages)],
                ("Element", "Total"): [len(self.prev.Elements), len(curr.Elements)],
                ("Element", "Added"): ["-", len(added)],
                ("Element", "Deleted"): [len(deleted), "-"]
            },
            index=['Base Model', ' New Model']
        )
        self.logger.info(">>> Summary\n" + \
                         desc.to_string() + '\n' + \
                         f'* Added: {", ".join(added)}' + '\n' + \
                         f'* Deleted: {", ".join(deleted)}')
        return

    def collect_properties(self) -> DataDictionary:
        mainE = self.main.dataframe('Element').set_index(keys='OID').copy()
        implE = self.impl.dataframe('ImplementationEntry').set_index(keys='elementOID').copy()
        dataE = self.data.dataframe('DataEntry').set_index(keys='elementOID').copy()
        implE = implE.drop(columns=[col for col in implE if col in mainE.columns])
        dataE = dataE.drop(columns=[col for col in dataE if col in mainE.columns or col in implE.columns])
        return DataDictionary(
            MethodSignature=self.main.dataframe('MethodSignature').set_index(keys='OID'),
            MethodBody=self.spec.datadict('MethodBody'),
            HeaderBlock=self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('HeaderBlock').text,
            Elements=mainE.join(implE).join(dataE)
        )

    def parents(self, tag:str) -> Union[Any, Tuple]:
        if tag == "MethodSignature":
            return self.main.find('Component/MethodSignatures'), None
        if tag == "Element":
            return self.main.find('Component/Elements'), None
        if tag == 'ImplementationEntry':
            return tuple(self.impl.findall('ImplementationSet'))
        if tag == 'DataEntry':
            return tuple(self.data.findall('DataSet'))
        if tag == 'MethodBody':
            return self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies'), \
                   self.spec.strictFind('CodeVariant', target="PC").find('MethodBodies')
        if tag == "HeaderBlock":
            return self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('HeaderBlock'), \
                   self.spec.strictFind('CodeVariant', target="PC").find('HeaderBlock')
        raise AttributeError

    def define_elements(self, tag:str):
        """
        {tag}에 해당하는 AmdIO를 찾는다.
        {tag}에 해당하는 AmdIO의 부모 tag를 찾는다.
        - Implementation 및 Data는 @scope에 따른 부모 tag가 2개 존재한다.
        부모 tag의 하위 {tag}를 모두 삭제하고 신규 정의 Element로 대체한다.

        :param tag:
        :return:
        """
        pGlob, pLoc = self.parents(tag)
        for child in list(pGlob):
            pGlob.remove(child)
        if pLoc is not None:
            for child in list(pLoc):
                pLoc.remove(child)

        if tag == 'MethodSignature':
            for name in self.db.messages:
                pGlob.append(self.ME[name].method)
            return

        if tag == 'HeaderBlock':
            pLoc.text = "/* Please Change Target In Order To View Source Code */"
            pGlob.text = f"""#include <Bsw/Include/Bsw.h>

#ifdef SRV_HMCEMS
{"&lf;".join([mc.srv_name(self.name) for mc in self.MC.values()])}
#endif

{"&lf;".join([mc.def_name for mc in self.MC.values()])}

{"&lf;".join([mc.struct for mc in self.MC.values()])}
{_db2code.INLINE}""" \
    .replace("&tb;", "\t") \
    .replace("&lf;", "\n")
            if self.engine_spec == "HEV":
                pGlob.text = pGlob.text.replace("YRS", "IMU")
            return

        if tag == "MethodBody":
            for name, me in self.ME.items():
                method_body = self.ME[name].MethodBody
                dummy_method = copy.deepcopy(method_body)
                dummy_method.find("CodeBlock").text = ""
                pGlob.append(method_body)
                pLoc.append(dummy_method)
            return

        for se in self.SE:
            pGlob.append(getattr(se, tag))

        for key in _db2elem.MessageElement.__slots__:
            if key in ["method", "MethodBody", "aliveCounter", "crc"]:
                continue
            for name, me in self.ME.items():
                if hasattr(me, key):
                    elem = getattr(me, key)
                    if pLoc is None:
                        parent = pGlob
                    else:
                        parent = pLoc if elem.kwargs.scope == "local" else pGlob
                    parent.append(getattr(elem, tag))

        parent = pGlob if tag == 'Element' else pLoc
        parent.append(getattr(_db2elem.crcClassElement(16, self.oids), tag))
        parent.append(getattr(_db2elem.crcClassElement(8, self.oids), tag))
        return

    def export(self):
        self.main.export_to_downloads()
        self.impl.export_to_downloads()
        self.data.export_to_downloads()
        self.spec.export_to_downloads()
        return


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    db = CANDBReader()
    # db = CANDBReader(env.SVN_CANDB / rf'dev/G-PROJECT_KEFICO-EMS_CANFD_r21676@01.json')

    engine_spec = "HEV"

    # DB CUSTOMIZE ------------------------------------------------------
    # exclude_ecus = ["EMS", "CVVD", "MHSG", "NOx"]
    # if engine_spec == "ICE":
    #     exclude_ecus += ["BMS", "LDC"]
    # db = db[~db["ECU"].isin(exclude_ecus)]

    # db = db[db["Status"] != "TSW"] # TSW 제외
    # db = db[~db["Requirement ID"].isin(["VCDM CR10777888"])] # 특정 CR 제외
    # db = db[~db["Required Date"].isin(["2024-08-27"])] # 특정 일자 제외
    # db = db[~db["Message"].isin([ # 특정 메시지 제외
    #     "L_H8L_01_10ms",
    #     "H8L_01_10ms",
    #     "H8L_02_10ms",
    # ])]
    # db.revision = "TEST SW" # 공식SW는 주석 처리
    # DB CUSTOMIZE END --------------------------------------------------

    # model = ComDef(
    #     db=db,
    #     engine_spec=engine_spec,
    #     exclude_tsw=True,
    #     # base_model="",
    #     # base_model=r'D:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\StandardDB\NetworkDefinition\ComDef\ComDef-22368\ComDef.main.amd'
    #     # base_model=ENV['ASCET_EXPORT_PATH']
    # )
    # model.autorun()

    model = ComDef(
        db=db,
        engine_spec=engine_spec,
        exclude_tsw=True,
        # base_model=env.ASCET / f"Export/ComDef_G/ComDef_G.main.amd"
    )
    model.autorun()