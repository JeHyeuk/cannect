from cannect.config import env
from cannect.core.ascet.oid import generateOID
from cannect.core.ascet.amd import AmdElements
from cannect.core.ascet.formula import formula_dictionary
from cannect.core.can.ascet import _db2code
from cannect.core.can.rule import naming
from cannect.schema.candb import CanMessage, CanSignal
from cannect.schema.datadictionary import DataDictionary
from cannect.utils.tools import xml

from typing import Dict, Iterator, Optional, Union
from xml.etree.ElementTree import Element
import math


F = None
def elementWrapper(**kwargs) -> DataDictionary:
    return DataDictionary(
        kwargs=DataDictionary(**kwargs),
        Element=AmdElements.Element(**kwargs),
        ImplementationEntry=AmdElements.ImplementationEntry(**kwargs),
        DataEntry=AmdElements.DataEntry(**kwargs)
    )


def crcClassElement(n:Union[int, str], oid_tag:Optional[Dict[str, str]]=None) -> DataDictionary:
    n = str(n)
    if not oid_tag:
        oid_tag = {}
    class_id = DataDictionary(
        componentID={
            "8": "_040g1ngg01pp1oo708cg4rviuqor2",
            "16": "_040g1ngg01pp1oo708a0du6locrr2"
        },
        implementationOID={
            "8": "_040g1ngg01pp1oo708cg4rviur2r2",
            "16": "_040g1ngg01pp1oo708a0du6lq95b2"
        },
        dataOID={
            "8": "_040g1ngg01pp1oo708cg4rviuqvb2",
            "16": "_040g1ngg01pp1oo708a0du6lod1r2"
        }
    )
    name = f'CRC{n}bit_Calculator'
    kwargs = DataDictionary(
        name=name,
        OID=oid_tag[name] if name in oid_tag else generateOID(),
        comment=f'CRC {n}bit Calculator Instance',
        modelType="complex",
        basicModelType="class",
        unit="",
        componentName=f"/HNB_GASOLINE/_29_CommunicationVehicle/CANInterfaceCommon/InterfaceLibrary/CRCCalc/"
                      f"CRC{n}Bit_Calculator/CRC{n}bit_Calculator",
        componentID=class_id.componentID[n],
        scope="local",
        set="false",
        get="false",
        read="true",
        write="true",
        reference="false",
        elementName=f'CRC{n}bit_Calculator',
        elementOID="",
        implementationName="Impl",
        implementationOID=class_id.implementationOID[n],
        value="false",
        dataName="Data",
        dataOID=class_id.dataOID[n]
    )
    return elementWrapper(**kwargs)


def SignalElement(signal:CanSignal, oid_tag:Optional[Dict[str, str]]=None) -> DataDictionary:
    global F
    if F is None:
        F = formula_dictionary(env.SVN_CAN / "CAN_Model/Formula/HNB_I4GDI_I4MPI.xml")

    if not oid_tag:
        oid_tag = {}
    kwargs = DataDictionary()
    element_name = signal.name if not signal["SignalRenamed"] else signal["SignalRenamed"]
    kwargs.name = name = f'{element_name}_{"Ems" if signal.ECU == "EMS" else "Can"}'
    kwargs.OID = oid_tag[name] if name in oid_tag else generateOID()
    kwargs.comment = signal.Definition
    if signal.ECU == "EMS":
        kwargs.comment = ""
    kwargs.modelType = 'scalar'
    if signal.Length == 1:
        kwargs.basicModelType = "log"
    elif signal.Formula == "OneToOne":
        kwargs.basicModelType = "udisc"
    else:
        kwargs.basicModelType = 'cont'
    kwargs.unit = signal.Unit

    kwargs.kind = "message"
    kwargs.scope = "exported"
    if signal.ECU == "EMS":
        kwargs.scope = "imported"
        if signal.isCrc() or signal.isAliveCounter():
            kwargs.scope = "local"

    kwargs.quantization = "0" if kwargs.basicModelType == "cont" else "1"
    kwargs.formula = signal.Formula

    size = 8 if signal.Length <= 8 else 16 if signal.Length <= 16 else 32
    kwargs.physType = "real64" if kwargs.basicModelType == "cont" else "uint32"
    kwargs.implType = f"sint{size}" if signal["Value Type"].startswith("Signed") else f"uint{size}"
    kwargs.implMin = f"-{2 ** (size - 1)}" if signal["Value Type"].startswith("Signed") else "0"
    kwargs.implMax = f"{2 ** (size - 1) - 1}" if signal["Value Type"].startswith("Signed") else f"{2 ** size - 1}"

    if not signal.Formula in F:
        min_val = int(kwargs.implMin) * signal.Factor + signal.Offset
        max_val = int(kwargs.implMax) * signal.Factor + signal.Offset
    else:
        f = F[signal.Formula]
        min_val = int(kwargs.implMin) * f.quantization + f.offset
        max_val = int(kwargs.implMax) * f.quantization + f.offset

    kwargs.physMin = f"{min_val}" if kwargs.basicModelType == "cont" else f"{int(min_val)}"
    kwargs.physMax = f"{max_val}" if kwargs.basicModelType == "cont" else f"{int(max_val)}"
    if str(signal.name).startswith("FPCM_ActlPrsrVal"):
        kwargs.physMax = "800.0"
    if str(signal.name).startswith("TCU_GrRatioChngProg"):
        kwargs.physMax = "1.0"


    kwargs.value = "false" if kwargs.basicModelType == "log" else "0.0" if kwargs.basicModelType == "cont" else "0"
    return elementWrapper(**kwargs)


class MessageElement:

    __slots__ = [
        "method",
        "MethodBody",
        "buffer",
        "dlc",
        "thresholdTime",
        "counter",
        "counterCalc",
        "messageCountTimer",
        "messageCountValid",
        "aliveCounter",
        "aliveCounterCalc",
        "aliveCountTimer",
        "aliveCountValid",
        "crc",
        "crcCalc",
        "crcTimer",
        "crcValid",
    ]

    def __init__(self, message:CanMessage, oid_tag:Optional[Dict[str, str]]=None):
        if not oid_tag:
            oid_tag = {}
        comment_id = f'{message.name}({message["ID"]})'
        timer_formula = f"Ti_q{str(message['taskTime']).replace('.', 'p')}_s".replace('p0_s', '_s')
        timer_round = 3 if message["taskTime"] == 0.001 else 2
        """
        신규 Element OID 부여
        """
        rule = naming(message.name)
        for req in self.__slots__:
            if req.startswith("MethodBody"):
                continue
            if req == "aliveCounter":
                oid_tag[f'{message.aliveCounter.name}_Can'] = oid_tag.get(f'{message.aliveCounter.name}_Can', '') or generateOID()
                continue
            if req == "aliveCounterCalc":
                oid_tag[f'{message.aliveCounter.name}Calc'] = oid_tag.get(f'{message.aliveCounter.name}Calc', '') or generateOID()
                continue
            if req == "crc":
                oid_tag[f'{message.crc.name}_Can'] = oid_tag.get(f'{message.crc.name}_Can', '') or generateOID()
                continue
            if req == 'crcCalc':
                oid_tag[f'{message.crc.name}Calc'] = oid_tag.get(f'{message.crc.name}Calc', '') or generateOID()
                continue

            if not oid_tag or not getattr(rule, req) in oid_tag:
                oid_tag[getattr(rule, req)] = generateOID()

        """
        %ComDef* 모델의 메시지 MethodSignature 생성
        """
        self.method = AmdElements.MethodSignature(
            name=rule.method,
            OID=oid_tag[rule.method],
            defaultMethod='true' if str(message.name) == 'ABS_ESC_01_10ms' else 'false'
        )

        """
        %ComDef* 모델의 메시지에 대한 MethodBody의 CodeBlock :: C Code 소스
        """
        MethodBody = Element('MethodBody', methodName=rule.method, methodOID=oid_tag[rule.method])
        CodeBlock = Element('CodeBlock')
        CodeBlock.text = _db2code.MessageCode(message).method
        MethodBody.append(CodeBlock)
        self.MethodBody = MethodBody

        """
        %ComDef* 모델의 메시지 Element
        """
        self.buffer = elementWrapper(**DataDictionary(
            name=rule.buffer,
            OID=oid_tag[rule.buffer],
            comment=f'{comment_id} Buffer',
            modelType="array",
            basicModelType="udisc",
            maxSizeX=str(message["DLC"]),
            kind="variable",
            scope="exported",
            quantization="1",
            formula="OneToOne",
            physType="uint32", physMin="0", physMax="255",
            implType="uint8", implMin="0", implMax="255",
            value="0",
        ))

        self.dlc = elementWrapper(**DataDictionary(
            name=rule.dlc,
            OID=oid_tag[rule.dlc],
            comment=f'{comment_id} DLC',
            modelType="scalar",
            basicModelType="udisc",
            kind="variable",
            scope="local",
            quantization="1",
            formula="OneToOne",
            physType="uint32", physMin="0", physMax="255",
            implType="uint8", implMin="0", implMax="255",
            value="0",
        ))

        self.thresholdTime = elementWrapper(**DataDictionary(
            name=rule.thresholdTime,
            OID=oid_tag[rule.thresholdTime],
            comment=f'{comment_id} Timeout Threshold',
            modelType="scalar",
            basicModelType="cont",
            unit="s",
            kind="parameter",
            scope="exported",
            volatile="false",
            write="false",
            quantization="0",
            formula=timer_formula,
            physType="real64", physMin="0.0", physMax=f'{round(255 * message["taskTime"], timer_round)}',
            implType="uint8", implMin="0", implMax="255",
            value=f'{math.ceil(message["timeoutTime"] / message["taskTime"]) * message["taskTime"]: .2f}'
        ))

        self.counter = elementWrapper(**DataDictionary(
            name=rule.counter,
            OID=oid_tag[rule.counter],
            comment=f'{comment_id} Message Counter',
            modelType="scalar",
            basicModelType="udisc",
            kind="message",
            scope="exported",
            quantization="1",
            formula="OneToOne",
            physType="uint32", physMin="0", physMax="255",
            implType="uint8", implMin="0", implMax="255",
            value="0",
        ))

        self.counterCalc = elementWrapper(**DataDictionary(
            name=rule.counterCalc,
            OID=oid_tag[rule.counterCalc],
            comment=f'{comment_id} Message Counter Calculated',
            modelType="scalar",
            basicModelType="udisc",
            kind="variable",
            scope="local",
            quantization="1",
            formula="OneToOne",
            physType="uint32", physMin="0", physMax="255",
            implType="uint8", implMin="0", implMax="255",
            value="0",
        ))

        self.messageCountTimer = elementWrapper(**DataDictionary(
            name=rule.messageCountTimer,
            OID=oid_tag[rule.messageCountTimer],
            comment=f'{comment_id} Counter Timeout Timer',
            modelType="scalar",
            basicModelType="cont",
            unit="s",
            kind="variable",
            scope="local",
            quantization="0",
            formula=timer_formula,
            physType="real64", physMin="0.0", physMax=f'{round(255 * message["taskTime"], timer_round)}',
            implType="uint8", implMin="0", implMax="255",
            value=f'0.0'
        ))

        self.messageCountValid = elementWrapper(**DataDictionary(
            name=rule.messageCountValid,
            OID=oid_tag[rule.messageCountValid],
            comment=f'{comment_id} Counter Validity',
            modelType="scalar",
            basicModelType="log",
            kind="message",
            scope="exported",
            physType="log",
            value="false"
        ))

        if message.hasAliveCounter():
            self.aliveCounter = SignalElement(message.aliveCounter, oid_tag)
            attr = xml.to_dict(self.aliveCounter.Element)
            attr.update(xml.to_dict(self.aliveCounter.ImplementationEntry))
            attr.update(xml.to_dict(self.aliveCounter.DataEntry))
            attr.update(
                name=f'{message.aliveCounter.name}Calc',
                OID=oid_tag[f'{message.aliveCounter.name}Calc'],
                comment=f'{comment_id} Alive Counter Calculated',
                kind='variable',
                scope='local'
            )
            self.aliveCounterCalc = elementWrapper(**attr)
            self.aliveCountTimer = elementWrapper(**DataDictionary(
                name=rule.aliveCountTimer,
                OID=oid_tag[rule.aliveCountTimer],
                comment=f'{comment_id} Alive Counter Timeout Timer',
                modelType="scalar",
                basicModelType="cont",
                unit="s",
                kind="variable",
                scope="local",
                quantization="0",
                formula=timer_formula,
                physType="real64", physMin="0.0", physMax=f'{round(255 * message["taskTime"], timer_round)}',
                implType="uint8", implMin="0", implMax="255",
                value=f'0.0'
            ))
            self.aliveCountValid = elementWrapper(**DataDictionary(
                name=rule.aliveCountValid,
                OID=oid_tag[rule.aliveCountValid],
                comment=f'{comment_id} Alive Counter Validity',
                modelType="scalar",
                basicModelType="log",
                kind="message",
                scope="exported",
                physType="log",
                value="false"
            ))

        if message.hasCrc():
            self.crc = SignalElement(message.crc, oid_tag)
            attr = xml.to_dict(self.crc.Element)
            attr.update(xml.to_dict(self.crc.ImplementationEntry))
            attr.update(xml.to_dict(self.crc.DataEntry))
            attr.update(
                name=f'{message.crc.name}Calc',
                OID=oid_tag[f'{message.crc.name}Calc'],
                comment=f'{comment_id} CRC Calculated',
                kind='variable',
                scope='local'
            )
            if message.name == "ESC_01_10ms":
                attr.update(
                    kind='message',
                    scope='exported',
                )
            self.crcCalc = elementWrapper(**attr)
            self.crcTimer = elementWrapper(**DataDictionary(
                name=rule.crcTimer,
                OID=oid_tag[rule.crcTimer],
                comment=f'{comment_id} Alive Counter Timeout Timer',
                modelType="scalar",
                basicModelType="cont",
                unit="s",
                kind="variable",
                scope="local",
                quantization="0",
                formula=timer_formula,
                physType="real64", physMin="0.0", physMax=f'{round(255 * message["taskTime"], timer_round)}',
                implType="uint8", implMin="0", implMax="255",
                value=f'0.0'
            ))

            self.crcValid = elementWrapper(**DataDictionary(
                name=rule.crcValid,
                OID=oid_tag[rule.crcValid],
                comment=f'{comment_id} CRC Validity',
                modelType="scalar",
                basicModelType="log",
                kind="message",
                scope="exported",
                physType="log",
                value="false"
            ))

        return

    def __iter__(self) -> Iterator[DataDictionary]:
        for slot in self.__slots__:
            yield self.__getattribute__(slot)


