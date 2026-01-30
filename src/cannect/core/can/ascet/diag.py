from cannect.config import env
from cannect.core.ascet.amd import Amd
from cannect.core.ascet.oid import generateOID
from cannect.core.ascet.ws import WorkspaceIO
from cannect.core.can.db.reader import CANDBReader
from cannect.core.can.ascet._db2code import INFO
from cannect.core.can.rule import naming
from cannect.utils import tools
from cannect.utils.logger import Logger

from typing import Dict, Tuple
from xml.etree.ElementTree import Element
import os, copy

from cannect.utils.tools import path_abbreviate


class CANDiag(Amd):

    def __init__(self, db: CANDBReader, src: str, *messages, **kwargs):

        for message in messages:
            if not message in db.messages:
                raise KeyError(f'{message} NOT EXIST IN CAN DB.')

        template = env.SVN_CAN / "CAN_Model/_29_CommunicationVehicle/StandardDB/StandardTemplate/CANDiagTmplt/CANDiagTmplt.main.amd"
        super().__init__(str(template))

        self.ws = WorkspaceIO()

        # LOGGER 생성
        base = Amd(src)

        self.logger = Logger()
        self.logger(f"%{{{base.name}}} MODEL GENERATION")
        self.logger(f">>> DB VERSION: {db.revision}")
        self.logger(f">>> BASE MODEL: {tools.path_abbreviate(src)}")
        if "revision" in kwargs:
            self.logger(f">>> MODEL REVISION: {kwargs['revision']}")

        # @self.n        : 메시지 순번
        # @self.db       : CAN DB 객체
        # @self.messages : 메시지 이름 리스트
        self.n, self.db, self.messages = 1, db, list(messages)

        # @self.tx : 송출처 이름(Legacy); ABS, BMS, TCU, ...
        # @self.hw : 차량 프로젝트 타입; HEV, ICE
        # @self.cal: Default Cal. 데이터(값)
        self.tx, self.hw, self.cal = self.read_from_basemodel(base)

        self.manual_instruction = []
        self.base = base
        return

    @classmethod
    def read_from_basemodel(cls, base: Amd) -> Tuple[str, str, Dict]:
        """
        BASE 모델의 송출처, 타입, Cal. 값 읽기
        """
        tx = base.name \
             .replace("_HEV", "") \
             .replace("_48V", "") \
             .replace("CanFD", "") \
             .replace("CanHS", "") \
             .replace("Can", "")[:-1]
        hw = "HEV" if "HEV" in base.name else "ICE"
        cal = {}
        for elem in base.main.iter('Element'):
            attr = elem.find('ElementAttributes/ScalarType/PrimitiveAttributes')
            if attr is not None:
                if attr.get('scope', '') == 'imported':
                    continue
                if attr.get('kind', '') == 'parameter':
                    data = base.data.strictFind('DataEntry', elementName=elem.get('name'))
                    cal[elem.get('name')] = list(data.iter('Numeric'))[0].get('value')
        return tx, hw, cal

    def copy_from_basemodel(self, base: Amd):
        """
        BASE 모델의 기본 정보들을 CANDiag으로 복사
        """
        log = ''

        # [ 모델 Comment 생성 ]
        # <ComponentMain  toolVersion="V6.1.0-Win10" schemaVersion="6.1.0.0">
        #     <Component * >
        #         <TimeStamp * />
        #         <Comment>{ 이 자리의 Comment 생성 }</Comment>
        #    </Component>
        #    ...
        # </ComponentMain>
        message_list = "[MESSAGE LIST]\n- " + "\n- ".join(self.messages)
        self.main.find('Component/Comment').text = f"{INFO(self.db.revision)}{message_list}"

        # [ Base 모델의 *.main.amd 기본 정보 복사 ]
        # <ComponentMain  toolVersion="V6.1.0-Win10" schemaVersion="6.1.0.0">
        #     <Component { 이 자리의 Attribute 복사 } >
        #         ...
        #     </Component>
        #     ...
        # </ComponentMain>
        self.name = self.main.name = base.main['name']
        self.main['name'] = base.main['name']
        self.main['nameSpace'] = base.main['nameSpace']
        self.main['OID'] = base.main['OID']
        try:
            self.main['defaultProjectName'] = base.main['defaultProjectName']
            self.main['defaultProjectOID'] = base.main['defaultProjectOID']
        except KeyError:
            self.main['defaultProjectName'] = f'{self.name}_DEFAULT'
        self.main.digestValue = base.main.digestValue
        self.main.signatureValue = base.main.signatureValue


        # [ Base 모델의 *.main.amd Method OID 정보 복사 ]
        # 대상 Method: ▲_100msRun ▲_Init ▲_fcmclr ▲_EEPRes ▲ClearDTCFilter ▲SetDTCFilter
        # Base 모델의 예외적 Method는 차후 처리한다.
        # <ComponentMain  toolVersion="V6.1.0-Win10" schemaVersion="6.1.0.0">
        #     <Component * >
        #         ...
        #         <Elements>
        #             ...
        #         </Elements>
        #         <MethodSignatures>
        #             <MethodSignature name="_100msRun" OID="{ 이 자리의 OID 복사 }" />
        #             ...
        #         </MethodSignatures>
        #     </Component>
        #     ...
        # </ComponentMain>
        base_method = base.main.dataframe('MethodSignature', depth='shallow')[['name', 'OID']]
        base_method = dict(zip(base_method['name'], base_method['OID']))
        for method in self.main.iter('MethodSignature'):
            if method.get('name') in base_method:
                method.set('OID', base_method[method.get('name')])

        # *.spec.amd
        for elem in self.spec.iter():
            if elem.get('methodName', '') in base_method:
                if 'methodOID' in elem.attrib:
                    elem.set('methodOID', base_method[elem.get('methodName')])

        # CANDiag에 정의되지 않은 MethodSignature 정보 복사
        main_method = [elem.get('name') for elem in self.main.iter('MethodSignature')]
        for elem in base.main.iter('MethodSignature'):
            if not elem.get('name') in main_method:
                if len(elem):
                    elem.remove(elem[0])
                self.main.strictFind('MethodSignatures').append(elem)
                self.spec.strictFind('MethodBodies').append(
                    Element('MethodBody', methodName=elem.get('name'), methodOID=elem.get('OID'))
                    # Element('MethodBody', methodName=elem.get('name'))
                )

        # *.implementation.amd 파일 정보 복사
        self.impl.name = base.main['name']
        self.impl['name'] = base.impl['name']
        self.impl['OID'] = base.impl['OID']
        self.impl.strictFind('ImplementationSet', name='Impl').attrib['OID'] = \
            base.impl.strictFind('ImplementationSet', name='Impl').attrib['OID']
        self.impl.digestValue = base.impl.digestValue
        self.impl.signatureValue = base.impl.signatureValue

        # *.data.amd 파일 정보 복사
        self.data.name = base.main['name']
        self.data['name'] = base.data['name']
        self.data['OID'] = base.data['OID']
        self.data.strictFind('DataSet', name='Data').attrib['OID'] = \
            base.data.strictFind('DataSet', name='Data').attrib['OID']
        self.data.digestValue = base.data.digestValue
        self.data.signatureValue = base.data.signatureValue

        # *.specification.amd 파일 정보 복사
        # BREAK 구문 존재 시, Hierarchy 및 관련 Element 복사
        self.spec.name = base.main['name']
        self.spec.digestValue = base.spec.digestValue
        self.spec.signatureValue = base.spec.signatureValue

        breaker = None
        for elem in base.spec.iter():
            if len(elem) and elem[0].tag != "Hierarchy":
                continue
            for _elem in elem.iter():
                if _elem.tag == 'Control' and _elem.get('type') == 'Break':
                    breaker = copy.deepcopy(elem)

        if breaker is not None:
            log = f'COPY BREAK HIERARCHY'
            elements = [elem.get('elementName') for elem in breaker.iter() if elem.get('elementName')]
            for elem in base.main.iter('Element'):
                if elem.get('name') in elements:
                    self.main.strictFind('Elements').append(elem)
            breaker[0].attrib['name'] = 'Break'
            breaker[0].find('Size').attrib['x'] = "40"
            breaker[0].find('Size').attrib['y'] = "40"
            breaker[0].find('Position').attrib['x'] = "110"
            breaker[0].find('Position').attrib['y'] = "280"
            breaker[0].find('LabelPosition').attrib['x'] = "110"
            breaker[0].find('LabelPosition').attrib['y'] = "260"
            self.spec.find('Specification/BlockDiagramSpecification/DiagramElements').append(breaker)
        return log

    def copy_common(self):
        pascal = self.tx.lower().capitalize()
        if self.tx.lower() == "nox":
            pascal = "NOx"
        if self.tx.lower() == "frcmr":
            pascal = "FrCmr"
        renamer = {
            f"CanD_cEnaDetBus1__TX_Pascal__": f"CanD_cEnaDetBus1{pascal}",
            f"CanD_cEnaDetBus2__TX_Pascal__": f"CanD_cEnaDetBus2{pascal}",
            f"CanD_cEnaDetBus3__TX_Pascal__": f"CanD_cEnaDetBus3{pascal}",
            f"CanD_ctDet__TX_Pascal___C": f"CanD_ctDet{pascal}_C",
            f"CanD_RstEep__TX_Pascal___C": f"CanD_RstEep{pascal}_C",
            f"CanD_tiMonDet__TX_Pascal___C": f"CanD_tiMonDet{pascal}_C",
            f"Cfg_Can__TX_UPPER__D_C": f"Cfg_CanFD{self.tx.upper()}D_C"
        }
        if self.name.endswith("_48V") or self.tx.upper() in ["CVVD", "FPCM"]:
            renamer[f"Cfg_Can__TX_UPPER__D_C"] = f"Cfg_Can{self.tx.upper()}D_C"
        if self.tx.upper() == "NOX":
            renamer[f"Cfg_Can__TX_UPPER__D_C"] = f"Cfg_Can{pascal}D_C"


        self.main.replace('Element', 'name', renamer)
        self.impl.replace('', 'elementName', renamer)
        self.data.replace('', 'elementName', renamer)
        self.spec.replace('', 'elementName', renamer)
        for elem in self.main.iter('Element'):
            if "__TX_UPPER__" in str(elem.find('Comment').text):
                elem.find('Comment').text = elem.find('Comment').text \
                                            .replace("__TX_UPPER__", self.tx.upper())
        return

    def copy_by_message(self, n:int, message:str):
        log = ''

        db = self.db.messages[message]
        nm = naming(message, self.hw)

        # 메시지 채널 결정
        chn = '1'
        if "_48V" in self.name:
            chn = '2'
        if (str(nm) == "FPCM_01_100ms") or str(nm).startswith("CVVD"):
            chn = '3'

        # 메시지 진단 타입 별 Hierarchy 복사 및 치환
        cp = "YY"
        if not db.hasCrc():
            cp = f"N{cp[1]}"
            log += f'NO CRC(DB) / '
        if db['Send Type'] == 'PE':
            cp = f"{cp[0]}N"
            log += f'NO A/C(PE TYPE) / '
        if not db.hasAliveCounter():
            cp = f"{cp[0]}N"
            log += f'NO A/C(DB) / '

        # 메시지 주기에 따른 Method 정의/교체
        method = self.main.dataframe('MethodSignature', depth='shallow')[['name', 'OID']]
        method = dict(zip(method['name'], method['OID']))
        method_name = f"_{int(max(db['Cycle Time'], 100))}msRun"
        if method_name in method:
            method_oid = method[method_name]
        else:
            method_oid = generateOID(1)
            new_method = copy.deepcopy(self.main.strictFind('MethodSignature', name='___M1_Task__msRun'))
            new_method.set('name', method_name)
            new_method.set('OID', method_oid)
            self.main.strictFind('MethodSignatures').append(new_method)
            new_method = Element('MethodBody', methodName=method_name)
            self.spec.strictFind('MethodBodies').append(new_method)
            self.manual_instruction.append(f'ADD IR/OS-TASK: {method_name}')

        # 메시지 순서 별 변수 이름 재정의
        pascal = self.tx.lower().capitalize()
        if self.tx.lower() == "nox":
            pascal = "NOx"
        replace_name = {
            f'CanD_cEnaDiagBus__M1_Chn__': f'CanD_cEnaDiagBus{chn}',
            f'CanD_cEnaDetBus__M1_Chn____TX_Pascal__': f'CanD_cEnaDetBus{chn}{pascal}',
            f"CanD_cEnaDiag__M1_Pascal__": nm.diagnosisEnable,
            f"CanD_cEnaDet__M1_Pascal__": nm.detectionEnable,
            f"CanD_cErr__M1_Pascal__Msg": nm.diagnosisMsg,
            f"CanD_ctDet__M1_Pascal__": nm.detectionCounter,
            f"CanD_stRdEep__M1_Pascal__": nm.eepReader,
            f"CanD_tiFlt__M1_Pascal___C": nm.debounceTime,
            f"CanD_tiFlt__M1_Pascal__Msg": nm.debounceTimerMsg,
            f"DEve_FD__M1_Pascal__Msg": nm.deveMsg,
            f"EEP_FD__M1_UPPER__": nm.eepIndex,
            f"EEP_stFD__M1_UPPER__": nm.eep,
            f"FD_cVld__M1_Pascal__Msg": nm.messageCountValid,
            f"Fid_FD__M1_UPPER__D": nm.fid
        }

        if cp[0] == 'Y':
            replace_name.update({
                f"CanD_cErr__M1_Pascal__Crc": nm.diagnosisCrc,
                f"CanD_tiFlt__M1_Pascal__Crc": nm.debounceTimerCrc,
                f"DEve_FD__M1_Pascal__Crc": nm.deveCrc,
                f"FD_cVld__M1_Pascal__Crc": nm.crcValid,
            })
        if cp[1] == 'Y':
            replace_name.update({
                f"CanD_cErr__M1_Pascal__Alv": nm.diagnosisAlv,
                f"CanD_tiFlt__M1_Pascal__Alv": nm.debounceTimerAlv,
                f"DEve_FD__M1_Pascal__Alv": nm.deveAlv,
                f"FD_cVld__M1_Pascal__Alv": nm.aliveCountValid,
            })
        replace_oid = {}

        # *.main.amd 요소 복사 및 치환
        main = self.main.strictFind('Elements')
        for pre, cur in replace_name.items():
            from_template = self.main.strictFind('Element', name=pre)
            required = self.main.strictFind('Element', name=cur)
            if not len(required):
                replace_oid[from_template.get('OID')] = oid = generateOID(1)
                copied = copy.deepcopy(from_template)
                copied.set('name', cur)
                copied.set('OID', oid)
                if "__M1_NAME__" in str(copied.find('Comment').text):
                    copied.find('Comment').text = copied.find('Comment').text \
                                                  .replace("__M1_NAME__", str(nm))
                main.append(copied)
            else:
                replace_oid[from_template.get('OID')] = required.get('OID')

        # *.implementation.amd 파일의 ImplementationEntry 요소를 복사
        # global 변수와 local 변수를 구분해서 복사함
        impl_global = self.impl.strictFind('ImplementationSet', name=self.name)
        impl_local = self.impl.strictFind('ImplementationSet', name='Impl')
        for pre, cur in replace_name.items():
            if self.impl.strictFind('elementName', name=cur):
                continue

            elem = self.main.strictFind('Element', name=cur)
            attr = elem.find('ElementAttributes/ScalarType/PrimitiveAttributes')
            if attr is not None and attr.get('scope') == 'imported':
                continue

            copied = copy.deepcopy(self.impl.strictFind('ElementImplementation', elementName=pre))
            copied.set('elementName', cur)
            copied.set('elementOID', elem.get('OID'))
            impl = Element('ImplementationEntry')
            impl.append(Element('ImplementationVariant', name='default'))
            impl[0].append(copied)
            if "EEP" in cur:
                impl_global.append(impl)
            else:
                impl_local.append(impl)

        # *.data.amd 파일의 DataEntry 요소를 복사
        # global 변수와 local 변수를 구분해서 복사함
        data_global = self.data.strictFind('DataSet', name=self.name)
        data_local = self.data.strictFind('DataSet', name='Data')
        for pre, cur in replace_name.items():
            if self.data.strictFind('elementName', name=cur):
                continue

            elem = self.main.strictFind('Element', name=cur)
            attr = elem.find('ElementAttributes/ScalarType/PrimitiveAttributes')
            if attr is not None and attr.get('scope') == 'imported':
                continue

            copied = copy.deepcopy(self.data.strictFind('DataEntry', elementName=pre))
            copied.set('elementName', cur)
            copied.set('elementOID', elem.get('OID'))
            if "EEP" in cur:
                data_global.append(copied)
            else:
                data_local.append(copied)

        if str(nm) == "FPCM_01_100ms":
            template = copy.deepcopy(self.spec.strictFind('Hierarchy', name=f'__FPCM_01_100ms__NN'))
        else:
            template = copy.deepcopy(self.spec.strictFind('Hierarchy', name=f'__M1_NAME__{cp}'))
        offset = max([int(tag.attrib.get('graphicOID', '0')) for tag in template.iter()])
        template.set('graphicOID', str(int(template.get('graphicOID')) + (n - 1) * offset))
        template.set('name', f'{nm}')
        if n <= 5:
            template.find("Position").set('x', "260")
            template.find("Position").set('y', str(100 + (n - 1) * 90))
            template.find("LabelPosition").set('x', "260")
            template.find("LabelPosition").set('y', str(80 + (n - 1) * 90))
        else:
            template.find("Position").set('x', "450")
            template.find("Position").set('y', str(100 + (n - 6) * 90))
            template.find("LabelPosition").set('x', "450")
            template.find("LabelPosition").set('y', str(80 + (n - 6) * 90))

        for elem in template.iter():
            if elem.tag == 'SequenceCall':
                if elem.get('methodName', '') == '_Init':
                    elem.set('sequenceNumber', str(int(elem.get('sequenceNumber')) + (n - 1) * 2))
                if elem.get('methodName', '') == '_fcmclr':
                    elem.set('sequenceNumber', str(int(elem.get('sequenceNumber')) + (n - 1) * 3))
                if elem.get('methodName', '') == '_EEPRes':
                    elem.set('sequenceNumber', str(int(elem.get('sequenceNumber')) + (n - 1) * 1))
                if elem.get('methodName', '') == '___M1_Task__msRun':
                    elem.set('sequenceNumber', str(int(elem.get('sequenceNumber')) + (n - 1) * 10))
                    elem.set('methodName', method_name)
                    elem.set('methodOID', method_oid)
                if elem.get('methodName', '') == '_100msRun':
                    elem.set('sequenceNumber', str(int(elem.get('sequenceNumber')) + (n - 1) * 10))
            if elem.tag == "Literal" and elem.get("value", "") == "__M1__":
                elem.set('value', str(n - 1))
            if elem.tag == "Text" and elem.text == "__M1_Comment__":
                elem.text = f"""[ {nm} ]
ID                 : {db['ID']}
PERIOD        : {db['Cycle Time']}
SEND TYPE   : {db['Send Type']}
CHANNEL     : {db[f'{self.hw} Channel']}-CAN
- DIAG.CRC : {db.hasCrc()}
- DIAG.A/C  : {db.hasAliveCounter()}"""
            if elem.get('elementName', '') in replace_name:
                elem.set('elementName', replace_name[elem.get('elementName')])
            if elem.get('elementOID', '') in replace_oid:
                elem.set('elementOID', replace_oid[elem.get('elementOID')])

        diagram = Element('DiagramElement')
        diagram.append(template)
        self.spec.find('Specification/BlockDiagramSpecification/DiagramElements').append(diagram)
        return log

    def clear(self):
        # CANDiag Hierarchy 제거
        removals = []
        for elem in self.spec.iter():
            try:
                if elem[0].get('name').startswith('__M1_NAME__') or \
                   elem[0].get('name') == '__FPCM_01_100ms__NN':
                    removals.append(elem)
            except (AttributeError, IndexError, KeyError):
                continue
        for diagram in removals:
            self.spec.find('Specification/BlockDiagramSpecification/DiagramElements').remove(diagram)

        # CANDiag Method 제거
        removals = []
        for elem in self.main.iter('MethodSignature'):
            if elem.get('name', '').startswith('___M1_Task__msRun'):
                removals.append(elem)
        for elem in removals:
            self.main.strictFind('MethodSignatures').remove(elem)
            self.spec.strictFind('MethodBodies') \
                .remove(self.spec.strictFind('MethodBody', methodName=elem.get('name')))

        used = []
        for tag in self.spec.iter():
            if 'elementName' in tag.attrib:
                used.append(tag.get('elementName'))

        # CANDiag Element 제거
        removals = []
        for elem in self.main.iter('Element'):
            if not elem.get('name') in used:
                removals.append(elem)
        for elem in removals:
            self.main.strictFind('Elements').remove(elem)

        for name in [self.name, 'Impl']:
            impl = self.impl.strictFind('ImplementationSet', name=name)
            removals = []
            for elem in impl.iter('ImplementationEntry'):
                if not elem[0][0].get('elementName') in used:
                    removals.append(elem)
                # if '__M1_' in elem[0][0].get('elementName', ''):
                #     removals.append(elem)
            for elem in removals:
                impl.remove(elem)

        for name in [self.name, 'Data']:
            data = self.data.strictFind('DataSet', name=name)
            removals = []
            for elem in data.iter('DataEntry'):
                if not elem.get('elementName') in used:
                # if '__M1_' in elem.get('elementName', ''):
                    removals.append(elem)
            for elem in removals:
                data.remove(elem)
        return

    def copy_dsm(self):
        fid_md = Amd(self.ws["Fid_Typ.zip"])
        fid = fid_md.impl.dataframe("ImplementationSet", depth="shallow").set_index("name")["OID"]
        deve_md = Amd(self.ws["DEve_Typ.zip"])
        deve = deve_md.impl.dataframe("ImplementationSet", depth="shallow").set_index("name")["OID"]

        for elem in self.impl.iter('ElementImplementation'):
            name = elem.attrib['elementName']
            if name.startswith("DEve"):
                impl_name = name.replace("DEve_", "") + "_DEve"
                lib = deve

            elif name.startswith("Fid"):
                impl_name = name.replace("Fid_", "") + "_Fid"
                lib = fid
            else:
                continue

            # MANUAL EXCEPTION CASE
            if self.hw == "ICE":
                if "AbsEsc" in impl_name:
                    impl_name = impl_name.replace("AbsEsc", "Abs")
                elif "HFEOP" in impl_name.upper():
                    impl_name = impl_name.replace("L", "")
                    if impl_name.endswith("Msg_DEve"):
                        impl_name = impl_name.replace("DEve", "Deve")
                elif "IlcuRh01" in impl_name:
                    impl_name = impl_name.replace("Ilcu", "ILcu")
                elif self.name.endswith("_48V"):
                    impl_name = impl_name.replace("FD", "Can") \
                                         .replace("State", "") \
                                         .replace("STATE", "") \
                                         .replace("Crc", "Chks")
                elif self.name == "CanCVVDD":
                    impl_name = impl_name.replace("FD", "Can") \
                                         .replace("Crc", "CRC")
            else:
                if impl_name.replace("0", "") in lib.index:
                    impl_name = impl_name.replace("0", "")

            if not impl_name in lib.index:
                self.manual_instruction.append(f'DSM MISSING: {impl_name}')
                continue
            elem[0].attrib.update({
                "implementationName": impl_name,
                "implementationOID": lib[impl_name]
            })
        return

    def copy_data(self):
        for data in self.data.iter('DataEntry'):
            if data.attrib.get('elementName', '') in self.cal:
                numeric = list(data.iter('Numeric'))[0]
                numeric.attrib['value'] = self.cal[data.attrib.get('elementName', '')]
        return

    def exception(self):

        def _change_attr(element_name: str, **change_attr):
            for elem in self.main.iter('Element'):
                if elem.attrib.get('name', '') == element_name:
                    attr = list(elem.iter('PrimitiveAttributes'))[0]
                    attr.attrib.update(change_attr)

            if change_attr.get('scope', '') == 'exported':
                objs = []
                for elem in self.impl.strictFind('ImplementationSet', name="Impl"):
                    ei = list(elem.iter('ElementImplementation'))
                    if ei and ei[0].attrib['elementName'] == element_name:
                        self.impl.strictFind('ImplementationSet', name=self.name).append(elem)
                        objs.append(elem)
                for obj in objs:
                    self.impl.strictFind('ImplementationSet', name="Impl").remove(obj)

                objs = []
                for elem in self.data.strictFind('DataSet', name="Data"):
                    if elem.attrib.get('elementName', '') == element_name:
                        self.data.strictFind('DataSet', name=self.name).append(elem)
                        objs.append(elem)
                for obj in objs:
                    self.data.strictFind('DataSet', name="Data").remove(obj)
            return

        if "_48V" in self.name:
            self.logger(f'>>> ... CHANGING DETECTION ENABLE SCOPE')
            detection = []
            for elem in self.main.iter('Element'):
                if elem.attrib['name'].startswith(f'CanD_cEnaDet{self.tx.lower().capitalize()}'):
                    detection.append(elem.attrib['name'])
            for var in detection:
                _change_attr(var, kind='message', scope='exported')

        elif self.name == "CanFDESCD":
            self.logger(f'>>> ... CHANGING DETECTION ENABLE SCOPE')
            rename = {'Cfg_FDESCD_C': 'Cfg_CanFDESCD_C'}
            self.main.replace('Element', 'name', rename)
            self.impl.replace('', 'elementName', rename)
            self.data.replace('', 'elementName', rename)
            self.spec.replace('', 'elementName', rename)

            _change_attr('CanD_cEnaDetEsc04', kind='message', scope='exported')
            _change_attr('Cfg_CanFDESCD_C', scope='exported')
            _change_attr('CanD_tiMonDetEsc_C', scope='exported')
        else:
            self.logger(f'>>> ... NO EXCEPTION FOUND')
        return

    def generate(self, path:str=''):

        # BASE 모델의 기본 정보들을 CANDiag으로 복사
        self.logger('>>> COPY BASE MODEL TO TEMPLATE')
        log = self.copy_from_basemodel(self.base)
        if log: self.logger(f'>>> ... {log}')

        # 공용 변수 Naming Rule 적용
        self.copy_common()

        # 메시지별 템플릿 적용
        self.logger(f'>>> GENERATE HIERARCHY BY MESSAGES N={len(self.messages)}')
        for n, message in enumerate(self.messages, start=1):
            log = self.copy_by_message(n, message)
            self.logger(f'>>> ... [{n} / {len(self.messages)}] {message}: {log}')

        # 템플릿 삭제
        self.clear()

        self.logger(f'>>> COPY DSM LIBRARY IMPLEMENTATION')
        self.copy_dsm()

        self.logger(f'>>> COPY CALIBRATION DATA FROM BASE MODEL')
        self.copy_data()

        self.logger(f'>>> RUN EXCEPTION HANDLING')
        self.exception()

        # 수동 예외처리 로그
        for instruction in self.manual_instruction:
            self.logger(f'>>> [MANUALLY] {instruction}')

        if not path:
            self.main.export_to_downloads()
            self.impl.export_to_downloads()
            self.data.export_to_downloads()
            self.spec.export_to_downloads()
            with open(os.path.join(env['DOWNLOADS'] / f'{self.name}/log.log'), 'w', encoding='utf-8') as f:
                f.write(self.logger.stream)
            self.logger(f'>>> CREATED TO "{path_abbreviate(env.DOWNLOADS / self.name)}" SUCCESS')
        else:
            self.main.export(path)
            self.impl.export(path)
            self.data.export(path)
            self.spec.export(path)
            with open(os.path.join(path, f'log.log'), 'w', encoding='utf-8') as f:
                f.write(self.logger.stream)
            self.logger(f'>>> CREATED TO "{path_abbreviate(path)}" SUCCESS')
        return


if __name__ == "__main__":
    from cannect.core.ascet.ws import WorkspaceIO
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    # ICE
    target = {
        "CanFDABSD": ["ABS_ESC_01_10ms", "WHL_01_10ms", ],
        "CanFDACUD": ["ACU_01_100ms", "IMU_01_10ms", ],
        "CanFDADASD": ["ADAS_CMD_10_20ms", "ADAS_CMD_20_20ms", "ADAS_PRK_20_20ms", "ADAS_PRK_21_20ms", ],
        "CanFDBCMD": ["BCM_02_200ms", "BCM_07_200ms", "BCM_10_200ms", "BCM_20_200ms", "BCM_22_200ms", ],
        "CanFDBDCD": ["BDC_FD_05_200ms", "BDC_FD_07_200ms", "BDC_FD_08_200ms", "BDC_FD_10_200ms",
                      "BDC_FD_SMK_02_200ms", ],
        "CanBMSD_48V": ["BMS5", "BMS6", "BMS7", ],
        "CanFDCCUD": ["CCU_OBM_01_1000ms", "CCU_OTA_01_200ms", ],
        "CanFDCLUD": ["CLU_01_20ms", "CLU_02_100ms", "CLU_18_20ms", ],
        "CanCVVDD": ["CVVD1", "CVVD2", "CVVD3", "CVVD4", ],
        "CanFDDATCD": ["DATC_01_20ms", "DATC_02_20ms", "DATC_07_200ms", "DATC_17_200ms", ],
        "CanFDEPBD": ["EPB_01_50ms", ],
        "CanFDESCD": ["ESC_01_10ms", "ESC_03_20ms", "ESC_04_50ms", ],
        "CanHSFPCMD": ["FPCM_01_100ms", ],
        "CanFDFRCMRD": ["FR_CMR_02_100ms", "FR_CMR_03_50ms", ],
        "CanFDHFEOPD": ["L_HFEOP_01_10ms", ],
        "CanFDHUD": ["HU_GW_03_200ms", "HU_GW_PE_01", "HU_OTA_01_500ms", "HU_OTA_PE_00", "HU_TMU_02_200ms", ],
        "CanFDICSCD": ["ICSC_02_100ms", "ICSC_03_100ms", ],
        "CanFDICUD": ["ICU_02_200ms", "ICU_04_200ms", "ICU_05_200ms", "ICU_07_200ms", "ICU_09_200ms", "ICU_10_200ms", ],
        "CanFDILCUD": ["ILCU_RH_01_200ms", "ILCU_RH_FD_01_200ms", ],
        "CanLDCD_48V": ["LDC1", "LDC2", ],
        "CanFDMDPSD": ["MDPS_01_10ms", "SAS_01_10ms", ],
        "CanMHSGD_48V": ["MHSG_STATE1", "MHSG_STATE2", "MHSG_STATE3", "MHSG_STATE4", ],
        "CanFDODSD": ["ODS_01_1000ms", ],
        "CanFDOPID": ["L_OPI_01_100ms", ],
        "CanFDPDCD": ["PDC_FD_01_200ms", "PDC_FD_03_200ms", "PDC_FD_10_200ms", "PDC_FD_11_200ms", ],
        "CanFDSBCMD": ["SBCM_DRV_03_200ms", "SBCM_DRV_FD_01_200ms", ],
        "CanFDSCUD": ["SCU_FF_01_10ms", ],
        "CanFDSMKD": ["SMK_05_200ms", ],
        "CanFDSWRCD": ["SWRC_03_20ms", "SWRC_FD_03_20ms", ],
        "CanFDLTCUD": ["L_TCU_01_10ms", "L_TCU_02_10ms", "L_TCU_03_10ms", "L_TCU_04_10ms", ],
        "CanFDTCUD": ["TCU_01_10ms", "TCU_02_10ms", "TCU_03_100ms", ],
        "CanFDTMUD": ["TMU_01_200ms", ],
        "CanNOXD": ["Main_Status_Rear", "O2_Rear"]
    }

    proj = WorkspaceIO()
    data = CANDBReader().to_developer_mode("HEV")

    template = CANDiag(data, proj["CanFDMCUD_HEV"], "MCU_01_P_10ms", "MCU_01_H_10ms", "MCU_02_P_10ms", "MCU_02_H_10ms", "MCU_03_100ms")
    template.generate()



