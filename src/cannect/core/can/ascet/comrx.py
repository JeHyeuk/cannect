from cannect.config import env
from cannect.core.ascet.amd import Amd
from cannect.core.can.ascet._db2code import MessageCode
from cannect.core.can.db.reader import CANDBReader
from cannect.utils.logger import Logger
from cannect.utils import tools

from typing import Dict
from pandas import DataFrame
import os


class ComRx:

    def __init__(
        self,
        db:CANDBReader,
        engine_spec:str,
        base_model:str='',
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
            name = f"ComRx{'_HEV' if engine_spec == 'HEV' else ''}"
            base_model = env.SVN_MODEL / rf'HNB_GASOLINE/_29_CommunicationVehicle/StandardDB/MessageInterface/MessageReceive/{name}/{name}.zip'
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

        (env.DOWNLOADS / name).mkdir(parents=True, exist_ok=True)
        self.logger = logger = Logger(env.DOWNLOADS / rf'{name}/log.txt', clean_record=True)
        logger.info(f"%{name} MODEL GENERATION")
        logger.info(f">>> Engine Spec : {engine_spec}")
        logger.info(f">>> Base Model  : {tools.path_abbreviate(base_model)}")
        logger.info(f">>> DB Revision : {db.revision}")

        prev = {
            method.attrib['methodName']: method.find('CodeBlock').text
            for method in list(spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies'))
        }
        curr = self.code_generation(host)
        self.spec_update(curr)

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

    def code_generation(self, host:str) -> Dict[str, str]:
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

    def spec_update(self, curr:Dict[str, str]):
        parent = self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies')
        for method in list(parent):
            name = method.attrib['methodName']
            method.find('CodeBlock').text = curr.get(name, "")
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
        # base_model=env.ASCET / f"Export/ComRx_G/ComRx_G.main.amd"
    )
    model.export()
