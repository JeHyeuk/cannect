from cannect.config import env
from cannect.core.ascet.amd import Amd
from cannect.core.ascet.ws import WorkspaceIO
from cannect.core.can.ascet._db2code import MessageCode, INFO
from cannect.core.can.db.api import DB
from cannect.utils.logger import Logger
from cannect.utils import tools

from pandas import DataFrame
from pathlib import Path
from typing import Dict, Union
import os


class ComRx:

    def __init__(
        self,
        db:DB,
        engine_spec:str,
        base_model:str='',
    ):
        exclude_ecus = ["EMS", "CVVD", "MHSG", "NOx"]
        if engine_spec == "ICE":
            exclude_ecus += ["BMS", "LDC"]
        db = db[~db["ECU"].isin(exclude_ecus)]

        if not db.is_developer_mode():
            db.to_developer_mode(engine_spec)

        if base_model:
            name = os.path.basename(base_model).split(".")[0]
        else:
            name = f"ComRx{'_HEV' if engine_spec == 'HEV' else ''}"
            base_model = WorkspaceIO()[name]
        host = name.replace("Rx", "Def")

        # 공용 속성 생성
        self.db = db
        self.name = name

        # 각 amd의 IO 생성
        amd = Amd(base_model)
        self.main = amd.main
        self.impl = amd.impl
        self.data = amd.data
        self.spec = spec = amd.spec

        # (env.DOWNLOADS / name).mkdir(parents=True, exist_ok=True)
        # self.logger = logger = Logger(env.DOWNLOADS / rf'{name}/log.log', clean_record=True)
        self.logger = logger = Logger(clean_record=True, console=False)
        logger.info(f"%{name} MODEL GENERATION")
        logger.info(f">>> Engine Spec : {engine_spec}")
        logger.info(f">>> Base Model  : {tools.path_abbreviate(base_model)}")
        logger.info(f">>> DB Revision : {db.rev}")

        unwanted_tag = spec.strictFind('CodeVariant', target="Default")
        if len(unwanted_tag):
            spec.findParent(unwanted_tag)[unwanted_tag].remove(unwanted_tag)

        prev = {
            method.attrib['methodName']: method.find('CodeBlock').text
            for method in list(spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies'))
        }
        curr = self._code_generation(host)
        self._spec_update(curr)

        summary_prev = MessageCode.method_contains_message(prev)
        summary_curr = MessageCode.method_contains_message(curr)
        deleted = list(set(summary_prev.index) - set(summary_curr.index))
        added = list(set(summary_curr.index) - set(summary_prev.index))
        desc = DataFrame(
            data={
                ("Message", "Total"): [len(summary_prev), len(summary_curr)],
                ("Message", "Added"): ["-", len(added)],
                ("Message", "Deleted"): [len(deleted), "-"]
            },
            index=['Base Model', ' New Model']
        )
        self.logger.info(">>> Summary\n" + \
                         desc.to_string() + '\n' + \
                         f'* Added: {", ".join(added)}' + '\n' + \
                         f'* Deleted: {", ".join(deleted)}')
        return

    def _code_generation(self, host:str) -> Dict[str, str]:
        context = {}
        for name, obj in self.db.messages.items():
            period = 40 if "E" in obj["Send Type"] else obj["Cycle Time"]
            key = f"_{period}msPreRunPost"
            if not key in context:
                context[key] = ""
            code = MessageCode(obj)
            context[key] += code.to_rx(host)

            if obj["WakeUp"]:
                key = f"_{period}msWakeUp"
                if not key in context:
                    context[key] = ""
                context[key] += code.to_rx(host)
        return context

    def _spec_update(self, curr:Dict[str, str]):
        parent = self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies')
        for method in list(parent):
            name = method.attrib['methodName']
            method.find('CodeBlock').text = curr.get(name, "")
        return

    def generate(self, path:Union[str, Path]=None):
        self.main.find('Component/Comment').text = INFO(self.db.rev)
        if path is None:
            self.main.export_to_downloads()
            self.impl.export_to_downloads()
            self.data.export_to_downloads()
            self.spec.export_to_downloads()
            with open(env.DOWNLOADS / rf'{self.name}/log.log', 'w', encoding='utf-8') as f:
                f.write(self.logger.stream)
        else:
            self.main.export(str(path))
            self.impl.export(str(path))
            self.data.export(str(path))
            self.spec.export(str(path))
            with open(Path(path) / 'log.log', 'w', encoding='utf-8') as f:
                f.write(self.logger.stream)
        return


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)


    db = DB()
    # db = CANDBReader(env.SVN_CANDB / rf'dev/G-PROJECT_KEFICO-EMS_CANFD_r21812@02.json')


    engine_spec = "ICE"

    # DB CUSTOMIZE ------------------------------------------------------
    # db = db[db["Status"] != "TSW"] # TSW 제외
    # db = db[~db["Requirement ID"].isin(["VCDM CR10777888"])] # 특정 CR 제외
    # db = db[~db["Required Date"].isin(["2024-08-27"])] # 특정 일자 제외
    # db = db[~db["Message"].isin([  # 특정 메시지 제외
    #     "L_H8L_01_10ms",
    #     "H8L_01_10ms",
    #     "H8L_02_10ms",
    # ])]
    # db.revision = "TEST SW" # 공식SW는 주석 처리
    # DB CUSTOMIZE END --------------------------------------------------

    model = ComRx(
        db=db,
        engine_spec=engine_spec,
        # base_model="",
        base_model=env.ASCET_PATH / f"Export/ComRx/ComRx.main.amd"
    )
    model.generate()
