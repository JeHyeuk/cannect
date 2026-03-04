from cannect.core.ascet.ws import WorkspaceIO
from cannect.core.ascet.oid import generateOID
from cannect.core.can.ascet._basemodel import _BaseModel
from cannect.core.can.ascet import _db2elem, _db2code
from cannect.core.can.ascet._db2elem import MessageElement, crcClassElement, SignalElement
from cannect.core.can.ascet._db2code import MessageCode, INFO, INLINE_MEMCPY
from cannect.core.can.db.reader import CANDBReader
from cannect.utils.logger import Logger
from cannect.utils import tools

from typing import Dict, List, Union
from pandas import DataFrame
from pathlib import Path
import os


class CanEMS(_BaseModel):

    def __init__(
        self,
        db:CANDBReader,
        base_model:Union[Path, str],
        messages:List[str]
    ):
        if not os.path.isfile(str(base_model)):
            base_model = WorkspaceIO()[base_model]
        super().__init__(base_model=base_model)

        if not db.is_developer_mode():
            engine_spec = "HEV" if "_HEV" in base_model else "ICE"
            db = db.to_developer_mode(engine_spec)

        # 공용 속성 생성
        self.db = db
        self.messages = messages

        self.logger = logger = Logger(self.path / 'log.txt', clean_record=True)
        logger.info(f"%{self.name} MODEL GENERATION")
        logger.info(f">>> Base Model  : {tools.path_abbreviate(base_model)}")
        logger.info(f">>> DB Revision : {db.revision}")

        # self.ME = {name: MessageElement(obj, oid_tag=oids) for name, obj in db.messages.items()}
        # prev = {
        #     method.attrib['methodName']: method.find('CodeBlock').text
        #     for method in list(spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies'))
        # }
        # curr = self._code_generation(host)
        # self._spec_update(curr)
        #
        # summary_prev = MessageCode.method_contains_message(prev)
        # summary_curr = MessageCode.method_contains_message(curr)
        # deleted = list(set(summary_prev.index) - set(summary_curr.index))
        # added = list(set(summary_curr.index) - set(summary_prev.index))
        # desc = DataFrame(
        #     data={
        #         ("Message", "Total"): [len(summary_prev), len(summary_curr)],
        #         ("Message", "Added"): ["-", len(added)],
        #         ("Message", "Deleted"): [len(deleted), "-"]
        #     },
        #     index=['Base Model', ' New Model']
        # )
        # self.logger.info(">>> Summary\n" + \
        #                  desc.to_string() + '\n' + \
        #                  f'* Added: {", ".join(added)}' + '\n' + \
        #                  f'* Deleted: {", ".join(deleted)}')
        return

    def _generate_element(self):
        self.clear_elements()
        self.logger('>>> Generating Elements ...')

        crc = []
        cfg, sys = False, False
        for msg in self.messages:
            obj = self.db.messages[msg]
            elem = MessageElement(obj, self.preserved.ObjectID)
            self.ElementsTag.append(elem.buffer.Element)
            self.ImplementationSetTag_Global.append(elem.buffer.ImplementationEntry)
            self.DataSet_Global.append(elem.buffer.DataEntry)

            self.ElementsTag.append(elem.dlc.Element)
            self.ImplementationSetTag_Local.append(elem.dlc.ImplementationEntry)
            self.DataSet_Local.append(elem.dlc.DataEntry)

            if obj.hasAliveCounter():
                sig = SignalElement(obj.aliveCounter, self.preserved.ObjectID)
                self.ElementsTag.append(sig.Element)
                self.ImplementationSetTag_Local.append(sig.ImplementationEntry)
                self.DataSet_Local.append(sig.DataEntry)

            if obj.hasCrc():
                crc.append(obj.crc.Length)
                sig = SignalElement(obj.crc, self.preserved.ObjectID)
                self.ElementsTag.append(sig.Element)
                self.ImplementationSetTag_Local.append(sig.ImplementationEntry)
                self.DataSet_Local.append(sig.DataEntry)

            if obj.syscon and not sys:
                name = ''.join([c for c in obj.syscon if (not c in ["=", "<", ">", " "]) and not c.isdigit()])
                e = self.preserved.Elements.copy()
                kwargs = e[e['name'] == name].iloc[0].fillna('').to_dict()
                kwargs['OID'] = generateOID(1)
                elem = _db2elem.elementWrapper(**kwargs)
                self.ElementsTag.append(elem.Element)
                sys = True

            if obj.codeword and not cfg:
                name = ''.join([c for c in obj.codeword if (not c in ["=", "<", ">", " "]) and not c.isdigit()])
                e = self.preserved.Elements.copy()
                kwargs = e[e['name'] == name].iloc[0].fillna('').to_dict()
                kwargs['OID'] = generateOID(1)
                elem = _db2elem.elementWrapper(**kwargs)
                self.ElementsTag.append(elem.Element)
                cfg = True

            obj.ITERATION_INCLUDES_CRC = obj.ITERATION_INCLUDES_ALIVECOUNTER = False
            for sig in obj:
                self.ElementsTag.append(SignalElement(sig, self.preserved.ObjectID).Element)

        for n in set(crc):
            obj = crcClassElement(n, self.preserved.ObjectID)
            self.ElementsTag.append(obj.Element)
            self.ImplementationSetTag_Local.append(obj.ImplementationEntry)
            self.DataSet_Local.append(obj.DataEntry)
        return

    def _write_header(self):
        self.logger('>>> Generating Codes ...')
        defs = ''
        tdef = ''
        for msg in self.messages:
            code = MessageCode(self.db.messages[msg])
            defs += f"{code.def_name}\n"
            tdef += f"{code.struct}\n\n"
        self.spec.strictFind('CodeVariant', target="PC").find('HeaderBlock').text \
            = "/* Please Change Target In Order To View Source Code */"
        self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('HeaderBlock').text \
            = f"#include <Bsw/Include/Bsw.h>\n\n{defs}{tdef}{INLINE_MEMCPY}\n"
        return

    def _write_method(self):
        methods = self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies')
        runstart = [method for method in methods.findall('MethodBody') if method.get('methodName') == '_RunStart'][0]
        for codeblock in self.spec.iter('CodeBlock'):
            codeblock.text = ''
        for msg in self.messages:
            code = MessageCode(self.db.messages[msg])
            period = 40 if "E" in code["Send Type"] else code["Cycle Time"]
            if code["Send Type"] in ["E", "EC", "EW"]:
                self.logger(f">>> [MANUAL] {msg} IS EVENT TYPE")
            key = f"_{period}msRunPost"
            for method in methods.findall('MethodBody'):
                if method.get('methodName', '') == key:
                    method.find('CodeBlock').text += code.send
            if code["WakeUp"]:
                # TODO
                pass
            runstart.find('CodeBlock').text += code.runstart
        return

    def generate(self):
        desc = self.main.find('Component/Comment')
        if not desc is None:
            desc.text = INFO(self.db.revision)

        self._generate_element()
        self._write_header()
        self._write_method()
        super().generate()
        return


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)
    from cannect import mount
    mount(r"E:\\SVN")

    db = CANDBReader()
    # db = CANDBReader(env.SVN_CANDB / rf'dev/G-PROJECT_KEFICO-EMS_CANFD_r21676@01.json')

    model = CanEMS(
        db=db,
        base_model="CanFDEMSO",
        messages=["PT_OBM_01_1000ms", "PT_OBM_02_00ms"]
    )
    model.generate()
