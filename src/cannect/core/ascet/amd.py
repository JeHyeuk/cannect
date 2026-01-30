from cannect.schema.datadictionary import DataDictionary
from cannect.errors import AmdFormatError
from cannect.config import env
from cannect.utils import tools

from datetime import datetime
from pandas import DataFrame, Series
from typing import Dict, List, Union
from xml.etree.ElementTree import ElementTree, Element
import os


class AmdSource(object):
    """
    [KOR]
    *.amd 파일 핸들러
    *.amd 파일을 읽기 위한 클래스입니다. *.main.amd, *.implementation.amd,
    *.data.amd, *.specification.amd 파일을 동일 경로에서 찾습니다. 입력된
    소스 파일이 압축 파일 (.zip)인 경우 임시 폴더(bin)에 압축을 푼 후 *.amd
    파일을 찾습니다. 임시 폴더는 정의하는 것을 강하게 권장합니다. 임시 폴더가
    정의되지 않은 경우 자동을 폴더 생성 후 클래스 인스턴스가 소멸될 때 삭제됩니다.

    [ENG]
    *.amd FILE HANDLER
    This class is designed to read *.amd files. It searches for related
    files such as: *.main.amd, *.implementation.amd, *.data.amd,
    *.specification.amd in the same directory as the input file. If the
    input source file is a compressed .zip file, it will be extracted to
    a temporary folder (default: 'bin'), and the *.amd files will be
    searched within the extracted contents. It is strongly recommended
    to explicitly define the temporary folder. If no temporary folder is
    defined, one will be automatically created. The folder will be deleted
    when the class instance is destroyed.
    """

    __slots__ = (
        "name", # name of *.amd
        "path", # directory (parent path) of *.amds
        "file", # full path of *.main.amd
        "main", # full path of *.main.amd
        "impl", # full path of *.implementation.amd
        "data", # full path of *.data.amd
        "spec", # full path of *.specification.amd
    )

    def __init__(self, file:str, binary:str=''):
        file = str(file)
        self.name = name = os.path.basename(file).split('.')[0]
        if file.endswith('.zip'):
            if not binary:
                binary = env.ASCET / "bin"
                os.makedirs(binary, exist_ok=True)
            tools.unzip(file, binary)
            self.path = path = binary
            self.file = file = os.path.join(binary, f'{name}.main.amd')
        elif file.endswith('.main.amd'):
            self.path = os.path.dirname(file)
            self.file = file
        else:
            raise AmdFormatError
        self.main = file
        self.impl = file.replace(".main.amd", ".implementation.amd")
        self.data = file.replace(".main.amd", ".data.amd")
        self.spec = file.replace(".main.amd", ".specification.amd")
        return

    def __del__(self):
        binary = os.path.join(os.path.dirname(__file__), 'bin')
        if os.path.exists(binary):
            tools.clear(binary, leave_path=False)



class AmdElements:
    """
    * NOTE *
    kwargs에 키값을 애트리뷰트(.)로 접근하는 경우 필수 키로 간주하며 *.get(attribute_name, default)로
    접근하는 경우, 키 값이 없어도 default로 치환하여 애트리뷰트를 생성함.
    """

    @classmethod
    def MethodSignature(cls, **kwargs) -> Element:
        """
        *.main.amd의 <MethodSignature> 요소 생성

        :param kwargs:
        :return:
        """
        kwargs = DataDictionary(**kwargs)
        return Element('MethodSignature',
                 name=kwargs.name,
                 OID=kwargs.OID,
                 public=kwargs.get('public', "true"),
                 default=kwargs.get('default', 'false'),
                 defaultMethod=kwargs.get('defaultMethod', 'false'),
                 hidden=kwargs.get('hidden', 'false'),
                 availableForOS=kwargs.get('availableForOS', 'true'))

    @classmethod
    def Element(cls, **kwargs) -> Element:
        """
        *.main.amd의 <Element> 요소 및 하위 요소 생성
        공통 태그 요소를 먼저 생성한 후 조건별 하위 태그 삽입

        예시 구조 :
            <Element name="Can_Wakeup01Size" OID="_040g1ngg01pp1og70ocg9t7rqsgg4" ignore="false">
              <Comment>WAKEUP_01_00ms(0x000) DLC</Comment>
                <ElementAttributes modelType="scalar" basicModelType="udisc" unit="">
                  # 여기에 @modelType에 따라 요소가 조건적으로 삽입됨
              </ElementAttributes>
            </Element>

        :param kwargs:
        :return:
        """
        kwargs = DataDictionary(**kwargs)

        """
        공통 태그 요소 생성
        """
        tElement = Element('Element',
                    name=kwargs.name,
                    OID=kwargs.OID,
                    ignore=kwargs.get('ignore', "false"))
        Comment = Element('Comment')
        if 'comment' in kwargs:
            Comment.text = kwargs.comment
        ElementAttributes = Element('ElementAttributes',
                              modelType=kwargs.modelType,
                              basicModelType=kwargs.basicModelType,
                              unit=kwargs.get('unit', ''))
        tElement.append(Comment)
        tElement.append(ElementAttributes)

        """
        basicModelType == 'implementationCast' 인 경우 추가 요소 삽입 없이 리턴
        """
        if kwargs.basicModelType == "implementationCast":
            return tElement

        """
        조건별 하위 태그 요소 삽입
        """
        if kwargs.modelType == "complex":
            """
            1. 클래스 요소
            """
            ComplexType = Element('ComplexType')
            ComplexAttribute = Element('ComplexAttributes',
                                 componentName=kwargs.componentName,
                                 componentID=kwargs.componentID,
                                 scope=kwargs.scope,
                                 set=kwargs.get('set', "false"),
                                 get=kwargs['get'] if 'get' in kwargs else 'false',
                                 read=kwargs.get('read', 'true'),
                                 write=kwargs.get('write', 'true'),
                                 reference=kwargs.get('reference', 'false'))
            ComplexType.append(ComplexAttribute)
            ElementAttributes.append(ComplexType)

        else:
            PrimitiveAttributes = Element('PrimitiveAttributes',
                                    kind=kwargs.kind,
                                    scope=kwargs.scope,
                                    virtual=kwargs.get('virtual', 'false'),
                                    dependent=kwargs.get('dependent', 'false'),
                                    volatile=kwargs.get('volatile', 'true'),
                                    calibrated=kwargs.get('calibrated', 'true'),
                                    set=kwargs.get('set', "false"),
                                    get=kwargs['get'] if 'get' in kwargs else 'false',
                                    read=kwargs.get('read', 'true'),
                                    write=kwargs.get('write', 'true'),
                                    reference=kwargs.get('reference', 'false'))

            if kwargs.modelType == 'scalar':
                """
                2. Scalar 요소
                """
                ScalarType = Element('ScalarType')
                ScalarType.append(PrimitiveAttributes)
                ElementAttributes.append(ScalarType)

            elif kwargs.modelType == 'array':
                """
                3. 배열 요소
                """
                DimensionalType = Element('DimensionalType',
                                    maxSizeX=kwargs.maxSizeX)
                DimensionalType.append(PrimitiveAttributes)
                ElementAttributes.append(DimensionalType)

            elif kwargs.modelType == 'oned':
                """
                4. 1-Dimensional Table 요소
                """
                # TODO
                pass

            elif kwargs.modelType == 'twod':
                """
                5. 2-Dimensional Table 요소
                """
                # TODO
                pass

            elif kwargs.modelType == 'distribution':
                """
                6. Distribution 요소
                """
                # TODO
                pass

            elif kwargs.modelType == 'matrix':
                """
                7. Matrix 요소
                """
                # TODO
                pass

            else:
                raise Exception(f'No Pre-defined <Element> for modelType = {kwargs.modelType}')
        return tElement

    @classmethod
    def ImplementationEntry(cls, **kwargs) -> Element:
        """
        *.implementation.amd의 <ImplementationEntry> 요소 및 하위 생성
        *.main.amd의 Element 생성 키워드를 C/O 하여야 한다. (종속적)

        공통 태그 요소를 먼저 생성한 후 조건별 하위 태그 삽입

        예시 구조 :
            <ImplementationEntry>
              <ImplementationVariant name="default">
                <ElementImplementation elementName="CRC16bit_Calculator" elementOID="_040g1ngg01401o8708804v4jlv5g4">
                  # 여기에 요소가 조건적으로 삽입됨
                </ElementImplementation>
              </ImplementationVariant>
            </ImplementationEntry>
        :param kwargs: Element(**kwargs)의 kwargs를 C/O
        :return:
        """
        kwargs = DataDictionary(**kwargs)

        ImplementationEntry = Element('ImplementationEntry')
        ImplementationVariant = Element('ImplementationVariant', name='default')
        ElementImplementation = Element('ElementImplementation',
                                  elementName=kwargs.name,
                                  elementOID=kwargs.OID)
        ImplementationVariant.append(ElementImplementation)
        ImplementationEntry.append(ImplementationVariant)

        """
            조건별 하위 태그 요소 삽입
            """
        if kwargs.modelType == "complex":
            """
            1. 클래스 요소
            """
            ComplexImplementation = Element('ComplexImplementation',
                                      implementationName=kwargs.implementationName,
                                      implementationOID=kwargs.implementationOID)
            ElementImplementation.append(ComplexImplementation)
        else:
            if kwargs.modelType == 'scalar':
                """
                2. Scalar 요소
                """
                ScalarImplementation = Element('ScalarImplementation')
                ElementImplementation.append(ScalarImplementation)

                if kwargs.basicModelType == 'implementationCast':
                    """
                    2-1. Impl. Cast 요소: CURRENTLY NOT USED
                    """
                    ImplementationCastImplementation = Element('ImplementationCastImplementation',
                                                         ignoreImplementationCast="false",
                                                         limitAssignments="true",
                                                         isLimitOverflow="true",
                                                         limitOverflow="automatic",
                                                         memoryLocationInstance="Default",
                                                         additionalInformation="",
                                                         cacheLocking="automatic",
                                                         quantization="0.1",
                                                         formula="TqPrpHigh_Nm",
                                                         master="Implementation",
                                                         physType="real64",
                                                         implType="sint32",
                                                         zeroNotIncluded="false")
                    ScalarImplementation.append(ImplementationCastImplementation)
                elif kwargs.basicModelType == 'log':
                    """
                    2-2. Log 타입 요소
                    """
                    LogicImplementation = Element('LogicImplementation',
                                            physType="log",
                                            implType="uint8",
                                            memoryLocationInstance="Default",
                                            additionalInformation="",
                                            cacheLocking="automatic")
                    ScalarImplementation.append(LogicImplementation)
                else:
                    """
                    2-3. 일반 Scalar 요소
                    """
                    NumericImplementation = Element('NumericImplementation',
                                              limitAssignments=kwargs.get("limitAssignments", "true"),
                                              isLimitOverflow=kwargs.get("isLimitOverflow", "true"),
                                              limitOverflow="automatic",
                                              memoryLocationInstance="Default",
                                              additionalInformation="",
                                              cacheLocking="automatic",
                                              quantization=kwargs.quantization,
                                              formula=kwargs.formula,
                                              master="Implementation",
                                              physType=kwargs.physType,
                                              implType=kwargs.implType,
                                              zeroNotIncluded="false")
                    ScalarImplementation.append(NumericImplementation)
                    PhysicalInterval = Element('PhysicalInterval',
                                         min=kwargs.physMin,
                                         max=kwargs.physMax)
                    NumericImplementation.append(PhysicalInterval)
                    ImplementationInterval = Element('ImplementationInterval',
                                               min=kwargs.implMin,
                                               max=kwargs.implMax)
                    NumericImplementation.append(ImplementationInterval)

            elif kwargs.modelType == 'array':
                """
                3. 배열 요소
                """
                DimensionalImplementation = Element('DimensionalImplementation')
                ElementImplementation.append(DimensionalImplementation)

                ArrayImplementation = Element('ArrayImplementation')
                DimensionalImplementation.append(ArrayImplementation)

                NumericImplementation = Element('NumericImplementation',
                                          limitAssignments=kwargs.get("limitAssignments", "true"),
                                          isLimitOverflow=kwargs.get("isLimitOverflow", "true"),
                                          limitOverflow="automatic",
                                          memoryLocationInstance="Default",
                                          additionalInformation="",
                                          cacheLocking="automatic",
                                          quantization=kwargs.quantization,
                                          formula=kwargs.formula,
                                          master="Implementation",
                                          physType=kwargs.physType,
                                          implType=kwargs.implType,
                                          zeroNotIncluded="false")
                ArrayImplementation.append(NumericImplementation)
                PhysicalInterval = Element('PhysicalInterval',
                                     min=kwargs.physMin,
                                     max=kwargs.physMax)
                NumericImplementation.append(PhysicalInterval)
                ImplementationInterval = Element('ImplementationInterval',
                                           min=kwargs.implMin,
                                           max=kwargs.implMax)
                NumericImplementation.append(ImplementationInterval)

            else:
                raise Exception(f'No Pre-defined <ImplementationEntry> for modelType = {kwargs.modelType}')

        return ImplementationEntry

    @classmethod
    def DataEntry(cls, **kwargs) -> Element:
        """
        *.data.amd의 <DataEntry> 요소 및 하위 생성
        *.main.amd의 Element 생성 키워드를 C/O 하여야 한다. (종속적)

        공통 태그 요소를 먼저 생성한 후 조건별 하위 태그 삽입

        예시 구조 :
            <DataEntry elementName="ABS_DfctvSta_Can" elementOID="_040g1ngg01a01o071c3g65u3aca0m">
    		  <DataVariant name="default">
                # 여기에 요소가 조건적으로 삽입됨
    		  </DataVariant>
    		</DataEntry>

        :param kwargs: Element(**kwargs)의 kwargs를 C/O
        :return:
        """
        kwargs = DataDictionary(**kwargs)

        DataEntry = Element('DataEntry',
                      elementName=kwargs.name,
                      elementOID=kwargs.OID)
        DataVariant = Element('DataVariant', name="default")
        DataEntry.append(DataVariant)

        """
        조건별 하위 태그 요소 삽입
        """
        if kwargs.modelType == "complex":
            """
            1. 클래스 요소
            """
            ComplexType = Element('ComplexType',
                            dataName=kwargs.dataName,
                            dataOID=kwargs.dataOID)
            DataVariant.append(ComplexType)
        else:
            if kwargs.modelType == 'scalar':
                """
                2. Scalar 요소
                """
                ScalarType = Element('ScalarType')
                DataVariant.append(ScalarType)
                if kwargs.basicModelType == 'implementationCast':
                    """
                    2-1. Impl. Cast 요소: CURRENTLY NOT USED
                    """
                    pass
                elif kwargs.basicModelType == 'log':
                    """
                    2-2. Log 타입 요소
                    """
                    Logic = Element('Logic', value=kwargs.get('value', 'false'))
                    ScalarType.append(Logic)
                else:
                    """
                    2-3. 일반 Scalar 요소
                    """
                    Numeric = Element('Numeric', value=kwargs.get('value', '0'))
                    ScalarType.append(Numeric)

            elif kwargs.modelType == 'array':
                """
                3. 배열 요소
                """
                DimensionalType = Element('DimensionalType')
                DataVariant.append(DimensionalType)

                Array = Element('Array', currentSizeX=kwargs.maxSizeX)
                DimensionalType.append(Array)

                Value = Element('Value')
                Numeric = Element('Numeric', value=kwargs.get('value', '0'))
                Value.append(Numeric)
                for n in range(int(kwargs.maxSizeX)):
                    Array.append(Value)

            else:
                raise Exception(f'No Pre-defined <ImplementationEntry> for modelType = {kwargs.modelType}')

        return DataEntry

    @classmethod
    def HeaderBlock(cls, **kwargs) -> Element:
        """
        *.specification.amd 의 C Code 에 대한 <HeaderBlock> 요소

        예시 구조 :
            <HeaderBlock>
              # 여기에 header의 Code 삽입
            </HeaderBlock>

        :param kwargs:
        :return:
        """
        HeaderBlock = Element("HeaderBlock")
        HeaderBlock.text = kwargs["code"] if "code" in kwargs else ""
        return HeaderBlock

    @classmethod
    def MethodBody(cls, **kwargs) -> Element:
        """
        *.specification.amd 의 C Code에 대한 <MethodBody> 요소 및 하위 요소

         예시 구조:
            <MethodBody methodName="_ABS_ESC_01_10ms" methodOID="_040g1ngg00p91o870o4g81ek53vj6">
              <CodeBlock>
                # 여기에 Code 삽입
              </CodeBlock>
    		</MethodBody>

        :param kwargs:
        :return:
        """
        MethodBody = Element('MethodBody', methodName=kwargs["methodName"], methodOID=kwargs["methodOID"])
        CodeBlock = Element('CodeBlock')
        CodeBlock.text = kwargs["code"] if "code" in kwargs else ""
        MethodBody.append(CodeBlock)
        return MethodBody



class AmdIO(ElementTree):

    def __init__(self, file:str):
        if file.endswith(".zip"):
            file = AmdSource(file).main
        super().__init__(file=file)
        self.path = file
        self.file = os.path.basename(file)
        self.name = os.path.basename(file).split(".")[0]
        self.type = self.getroot().tag

        if file.endswith('.main.amd'):
            self.extension = '.main.amd'
        elif file.endswith('.implementation.amd'):
            self.extension = '.implementation.amd'
        elif file.endswith('.data.amd'):
            self.extension = '.data.amd'
        elif file.endswith('.specification.amd'):
            self.extension = '.specification.amd'
        else:
            raise KeyError
        self._ns = {'ns0': 'http://www.w3.org/2000/09/xmldsig#'}
        return

    def __getitem__(self, item):
        return self.root[item]

    def __setitem__(self, key, value):
        if key in ['digestValue', 'signatureValue']:
            setattr(self, key, value)
            return
        if key in self.getroot()[0].attrib:
            self.getroot()[0].attrib[key] = value
        else:
            raise KeyError(f"No such attribute: {key}")

    @property
    def root(self) -> Series:
        """
        .amd 파일 메타데이터

        :return:
        """
        __attr__ = self.getroot()[0].attrib.copy()
        __attr__.update({
            'path': self.path,
            'file': self.file,
            'model': self.name,
            'type': self.type
        })
        return Series(data=__attr__)

    @property
    def digestValue(self) -> str:
        return self.find('ns0:Signature/ns0:SignedInfo/ns0:Reference/ns0:DigestValue', self._ns).text

    @digestValue.setter
    def digestValue(self, value: str):
        self.find('ns0:Signature/ns0:SignedInfo/ns0:Reference/ns0:DigestValue', self._ns).text = value

    @property
    def signatureValue(self) -> str:
        return self.find('ns0:Signature/ns0:SignatureValue', self._ns).text

    @signatureValue.setter
    def signatureValue(self, value: str):
        self.find('ns0:Signature/ns0:SignatureValue', self._ns).text = value

    def dataframe(self, tag:str, depth:str='recursive') -> DataFrame:
        df = DataFrame(data=self.datadict(tag, depth=depth))
        df['model'] = self.name
        return df

    def datadict(self, tag:str, depth:str='recursive') -> List[DataDictionary]:
        data = []
        for elem in self.iter():
            if elem.tag == tag:
                data.append(DataDictionary(tools.xml.to_dict(elem, depth=depth)))
        return data

    def export(self, path:str=''):
        if not path:
            # path = os.path.join(os.environ['USERPROFILE'], f'Downloads/{self.name}')
            path = os.path.dirname(self.path)
        timestamp = datetime.now().timestamp()
        os.makedirs(path, exist_ok=True)
        os.utime(path, (timestamp, timestamp))
        with open(file=os.path.join(path, f'{self.name}{self.extension}'), mode='w', encoding='utf-8') as f:
            f.write(self.serialize())
        return

    def export_to_downloads(self):
        self.export(path=os.path.join(os.environ['USERPROFILE'], f'Downloads/{self.name}'))
        return

    def findParent(self, *elems:Element) -> Dict[Element, Element]:
        parents = []
        for parent in self.iter():
            for child in list(parent):
                if any([id(child) == id(elem) for elem in elems]):
                    parents.append(parent)
        return dict(zip(elems, parents))

    def serialize(self) -> str:
        return tools.xml.to_str(self, xml_declaration=True)

    def strictFind(self, tag:str='', **attr) -> Union[Element, List[Element]]:
        found = []
        for node in self.iter():
            if tag:
                if not node.tag == tag:
                    continue

            if not attr:
                found.append(node)
                continue

            if all([node.attrib[key] == val for key, val in attr.items()]):
                found.append(node)
        if len(found) == 1:
            return found[0]
        return found

    def replace(self, tag:str='', attr_name:str='', attr_value:dict=None):
        if attr_value is None:
            return

        for elem in self.iter():
            if tag and elem.tag != tag:
                continue
            if not attr_name in elem.attrib:
                continue
            if not elem.attrib[attr_name] in attr_value:
                continue
            elem.attrib[attr_name] = attr_value[elem.attrib[attr_name]]
        return



class Amd:
    def __init__(self, file:str):
        sc = AmdSource(file)
        self.name = sc.name
        self.main = AmdIO(sc.main)
        self.impl = AmdIO(sc.impl)
        self.data = AmdIO(sc.data)
        self.spec = AmdIO(sc.spec)
        return


# Alias
AmdSC = AmdSource
AmdEL = AmdElements


if __name__ == "__main__":


    tester = r'D:\ETASData\ASCET6.1\Export\ComDef\ComDef.main.amd'
    amd = AmdIO(tester)
    # print(amd.root)
    # print(amd.serialize())
    # print(amd.export())
    print("*"*100)
    print(amd.digestValue)
    print(amd.signatureValue)


    # e = amd.strictFind('DataEntry', elementName="ABS_ActvSta_Can")
    # print(tools.xml.to_str(e, tools.xml_declaration=False))
    # parent = amd.findParent(e)
    # print(tools.xml.to_str(parent[e]))


    # amd.remove('DataEntry', elementName="CF_Ems_ActPurMotStat_VB_Ems")
    # amd.remove('DataEntry')
    # amd.remove(elementName='CF_Ems_ActPurEngOnReq_VB_Ems')
    # print(amd.dom)

    # amd.append(Element('Element', name='test', ))
    # print(amd.dom)

    # attr = DataDictionary(
    #     name='tester',
    #     OID="",
    #     # modelType='complex',
    #     # basicModelType='class',
    #     # modelType='scalar',
    #     # basicModelType='cont',
    #     modelType='array',
    #     basicModelType='udisc',
    #     scope='local',
    #
    #     componentName="classTester",
    #     componentID="",
    #     implementationName='Impl',
    #     implementationOID="",
    #     kind='message',
    #     quantization="0",
    #     formula="Test_Formula",
    #
    #     maxSizeX='8'
    #
    # )
    #
    # e = AmdElements.Element(**attr)
    # e = ImplementationEntry(**attr)
    # e = DataEntry(**attr)
    # print(tools.xml.to_str(e, tools.xml_declaration=False))