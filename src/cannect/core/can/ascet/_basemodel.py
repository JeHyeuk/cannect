from cannect.config import env
from cannect.core.ascet.amd import Amd
from cannect.schema.datadictionary import DataDictionary

from pandas import DataFrame, Series
from typing import Dict, Union
from xml.etree.ElementTree import Element

class _BaseModel(Amd):

    def __init__(self, base_model:str):
        super().__init__(file=base_model)

        self.path = env.DOWNLOADS / self.name
        self.path.mkdir(parents=True, exist_ok=True)

        self.preserved = DataDictionary(
            Elements=self.Elements,
            HeaderBlock=self.HeaderBlock,
            MethodBody=self.MethodBody,
            MethodSignature=self.MethodSignature,
            ObjectID=self.ObjectID,
        )
        return

    @property
    def Elements(self) -> DataFrame:
        _data = self.data.dataframe('DataEntry').set_index(keys='elementOID')
        _impl = self.impl.dataframe('ImplementationEntry').set_index(keys='elementOID')
        elements = self.main.dataframe('Element').set_index(keys='OID')
        elements = elements.join(_impl[_impl.columns.difference(elements.columns)])
        elements = elements.join(_data[_data.columns.difference(elements.columns)])
        return elements

    @property
    def HeaderBlock(self) -> Union[Element, None]:
        if self.main.root.get("specificationType", "") == "CCode":
            return self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('HeaderBlock')
        return None

    @property
    def MethodBody(self) -> Dict:
        return self.spec.datadict('MethodBody')

    @property
    def MethodSignature(self) -> DataFrame:
        return self.main.dataframe('MethodSignature').set_index(keys='OID')

    @property
    def ObjectID(self) -> Dict:
        return self.Elements['name'].reset_index().set_index('name')['OID'].to_dict()

    @property
    def ElementsTag(self) -> Element:
        return self.main.find('Component/Elements')

    @property
    def ImplementationSetTag_Global(self) -> Union[Element, None]:
        try:
            return self.impl.findall('ImplementationSet')[0]
        except IndexError:
            return None

    @property
    def ImplementationSetTag_Local(self) -> Union[Element, None]:
        try:
            return self.impl.findall('ImplementationSet')[1]
        except IndexError:
            return None

    @property
    def DataSet_Global(self) -> Union[Element, None]:
        try:
            return self.data.findall('DataSet')[0]
        except IndexError:
            return None

    @property
    def DataSet_Local(self) -> Union[Element, None]:
        try:
            return self.data.findall('DataSet')[1]
        except IndexError:
            return None

    def clear(self, tag:str):
        if 'element' in tag.lower():
            xml = [self.ElementsTag]
        elif 'implementation' in tag.lower():
            xml = tuple(self.impl.findall('ImplementationSet'))
        elif 'data' in tag.lower():
            xml = tuple(self.data.findall('DataSet'))
        elif 'methodsignature' in tag.lower():
            xml = [self.main.find('Component/MethodSignatures')]
        elif 'methodbody' in tag.lower():
            xml = self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('MethodBodies'), \
                  self.spec.strictFind('CodeVariant', target="PC").find('MethodBodies')
        elif 'header' in tag.lower():
            xml = self.spec.strictFind('CodeVariant', target="G_HMCEMS").find('HeaderBlock'), \
                  self.spec.strictFind('CodeVariant', target="PC").find('HeaderBlock')
        else:
            raise KeyError(f'Unknown tag type: {tag}')

        for _xml in xml:
            for child in list(_xml):
                if child.tag == "TimeStamp":
                    continue
                _xml.remove(child)
        return

    def clear_elements(self):
        self.clear('Elements')
        self.clear('ImplementationSet')
        self.clear('DataSet')
        return

    def generate(self):
        self.main.export_to_downloads()
        self.impl.export_to_downloads()
        self.data.export_to_downloads()
        self.spec.export_to_downloads()
        return


if __name__ == "__main__":
    from cannect.core.ascet.ws import WorkspaceIO

    ws = WorkspaceIO()
    base = _BaseModel(base_model=ws['CanFDEMSM01'])
    print(base.ObjectID)
