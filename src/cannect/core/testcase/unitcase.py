from cannect.config import env
from cannect.core.mdf import MdfReader
from cannect.core.testcase.style import Style
from cannect.core.testcase.plotter import Plot
from numpy import nan
from pandas import DataFrame, Series

from typing import Any, Union, List
from xlsxwriter import Workbook
import warnings, os

def custom_format(message, category, filename, lineno, line=None):
    return f"{message}\n"
warnings.formatwarning = custom_format

LABEL = {
    "NO": nan,
    "Category": "UNIT",
    "Group": "CAN",
    "Test Case - ID": '',
    "Test Case Name": '',
    "Requirement - Traceability": '',
    "Test Purpose, Description": '',
    "PreCondition (PC) - Description": "B+ / IG1",
    "PC-Variable": "BattU_u8\nIgKey_On",
    "PC-Compare": ">\n=",
    "PC-Value": "11.0\n1",
    "Test Execution (TE) - Description": '',
    "TE-Variable": '',
    "TE-Compare": '',
    "TE-Value": '',
    "Expected Results (ER) - Description": '',
    "ER-Variable": '',
    "ER-Compare": '',
    "ER-Value": '',
    "Test Result": '',
    "Test Result Description": '',
    "Test Conductor": f"{env.KOREANAME} @HYUNDAI-KEFICO",
    "Test SW": '',
    "Test HW": '',
    "Test Vehicle / Engine / HIL": '',
    "Test Environment": '',
    "Remark / Comment": '',
    "Measure / Log File (.dat)": '',
    "MDA Configuration File (.xda)": '',
    "Experiment File (.exp)": '',
    "VIO": '',
    "SWC": '',
    "MLT": "●",
    "SLT": '',
    "SDT": '',
    "FDT": '',
    "LVR": '',
    "DCV": '',
    "LSL": '',
    "PSV": '',
    "EOL": '',
}


class UnitTestCase(Series):

    __wb__:Workbook = None
    __dr__:MdfReader = None
    __pg__:str = ''

    def __init__(self, **kwargs):
        self.__wb__ = None
        self.__dr__ = None
        self.__pg__ = ''

        super().__init__({k: kwargs[k] if k in kwargs else v for k, v in LABEL.items()})
        if 'workbook' in kwargs:
            self.__wb__ = kwargs['workbook']
        return

    @property
    def workbook(self) -> Union[Any, Workbook]:
        return self.__wb__

    @workbook.setter
    def workbook(self, workbook: Workbook):
        self.__wb__ = workbook

    @property
    def mdf(self) -> MdfReader:
        return self.__dr__

    @mdf.setter
    def mdf(self, mdf:Union[str, MdfReader]):
        if isinstance(mdf, str):
            self.__dr__ = MdfReader(mdf)
        else:
            self.__dr__ = mdf
        self["Measure / Log File (.dat)"] = os.path.basename(self.__dr__.file)
        return

    @property
    def data(self) -> DataFrame:
        if self.__dr__ is None:
            return DataFrame()
        vars = []
        for var in self.variable:
            if var.startswith("DEve"):
                var = f"DEve_St.{var}"
            if var.startswith("Fid"):
                var = f"Fim_st.{var}"
            if not var in self.mdf:
                warnings.warn(
                    f'#{self["Test Case - ID"]}의 {var}(이)가 측정 파일: {self.mdf.file}내 없습니다.',
                    category=UserWarning
                )
                continue
            vars.append(var)
        return self.mdf[vars]

    @property
    def variable(self) -> List[str]:
        var = []
        for k, v in self.items():
            if not str(k).endswith("Variable") or str(v) in ["nan", '']:
                continue
            for _v in v.split("\n"):
                if not _v in var:
                    var.append(_v)
        return var

    @property
    def attachment(self) -> str:
        return self.__pg__

    @attachment.setter
    def attachment(self, attachment:str):
        self.__pg__ = attachment

    def figure(self, **kwargs) -> Plot:
        return Plot(self.data, **kwargs)

    def to_report(self, row:int=1):
        """
        @param row: [int] 시작 행 번호
        @param attach: [str] 그림 파일 경로
        """
        if isinstance(self.workbook, Workbook):
            wb = self.workbook
            ws = wb.worksheets_objs[0]
        else:
            # wb = self.workbook = Workbook(filename=PATH.DOWNLOADS.makefile(f"{self['Test Case Name']}.xlsx"))
            wb = self.workbook = Workbook(filename=env.DOWNLOADS / f"{self['Test Case Name']}.xlsx")
            ws = wb.add_worksheet(name="Test Report")
            ws.set_column('A:A', 1.63)
            for col in ["C", "F", "I", "L", "O"]:
                ws.set_column(f'{col}:{col}', 3.13)
            for col in ["B", "D", "E", "G", "H", "J", "K", "M", "N", "P"]:
                ws.set_column(f'{col}:{col}', 13)

        styler = Style(wb=wb, ws=ws)
        ws.merge_range(f'B{row}:C{row}', 'Test Category', styler.report_label["Category"])
        ws.merge_range(f'D{row}:E{row}', 'Test Group', styler.report_label["Group"])
        ws.merge_range(f'F{row}:H{row}', 'Test Case ID', styler.report_label["Test Case - ID"])
        ws.merge_range(f'I{row}:L{row}', 'Test Case Name', styler.report_label["Test Case Name"])
        ws.merge_range(f'M{row}:P{row}', 'Requirement - Traceability', styler.report_label["Requirement - Traceability"])
        ws.merge_range(f'B{row + 2}:D{row + 2}', 'Test Purpose', styler.report_label["Test Purpose, Description"])
        ws.merge_range(f'E{row + 2}:G{row + 2}', 'Pre-Condition', styler.report_label["PreCondition (PC) - Description"])
        ws.merge_range(f'H{row + 2}:J{row + 2}', 'Test Execution', styler.report_label["Test Execution (TE) - Description"])
        ws.merge_range(f'K{row + 2}:M{row + 2}', 'Expected Result', styler.report_label["Expected Results (ER) - Description"])
        ws.merge_range(f'N{row + 2}:P{row + 2}', 'Test Result', styler.report_label["Test Result"])
        ws.merge_range(f'B{row + 5}:L{row + 5}', 'Test Result Graph', styler.report_label["Test Result Graph"])
        ws.merge_range(f'M{row + 5}:P{row + 5}', '시험 결과 분석 / Comment / Remark', styler.report_label["Test Result Description"])
        ws.merge_range(f'B{row + 27}:D{row + 27}', 'Test Conductor', styler.report_label["Test Conductor"])
        ws.merge_range(f'E{row + 27}:G{row + 27}', 'Test SW', styler.report_label["Test SW"])
        ws.merge_range(f'H{row + 27}:J{row + 27}', 'Test HW', styler.report_label["Test HW"])
        ws.merge_range(f'K{row + 27}:M{row + 27}', 'Test Vehicle / Engine / HIL', styler.report_label["Test Case Name"])
        ws.merge_range(f'N{row + 27}:P{row + 27}', 'Test Environment', styler.report_label["Test Environment"])
        ws.merge_range(f'B{row + 29}:G{row + 29}', 'Remark / Comment', styler.report_label['Remark / Comment'])
        ws.merge_range(f'H{row + 29}:J{row + 29}', 'Measure / Log File (.dat)', styler.report_label['Measure / Log File (.dat)'])
        ws.merge_range(f'K{row + 29}:M{row + 29}', 'MDA Configuration File (.xda)', styler.report_label['MDA Configuration File (.xda)'])
        ws.merge_range(f'N{row + 29}:P{row + 29}', 'Experiment File (.exp)', styler.report_label['Experiment File (.exp)'])
        ws.merge_range(f'B{row + 1}:C{row + 1}', self['Category'], styler.report_value["Category"])
        ws.merge_range(f'D{row + 1}:E{row + 1}', self['Group'], styler.report_value["Group"])
        ws.merge_range(f'F{row + 1}:H{row + 1}', self['Test Case - ID'], styler.report_value["Test Case - ID"])
        ws.merge_range(f'I{row + 1}:L{row + 1}', self['Test Case Name'], styler.report_value["Test Case Name"])
        ws.merge_range(f'M{row + 1}:P{row + 1}', self['Requirement - Traceability'], styler.report_value["Requirement - Traceability"])
        ws.merge_range(f'B{row + 3}:D{row + 4}', self['Test Purpose, Description'], styler.report_value["Test Purpose, Description"])
        ws.merge_range(f'E{row + 3}:G{row + 3}', self['PreCondition (PC) - Description'], styler.report_value["PreCondition (PC) - Description"])
        ws.write(f'E{row + 4}', self['PC-Variable'], styler.report_value["PC-Variable"])
        ws.write(f'F{row + 4}', self['PC-Compare'], styler.report_value["PC-Compare"])
        ws.write(f'G{row + 4}', self['PC-Value'], styler.report_value["PC-Value"])
        ws.merge_range(f'H{row + 3}:J{row + 3}', self['Test Execution (TE) - Description'], styler.report_value["Test Execution (TE) - Description"])
        ws.write(f'H{row + 4}', self['TE-Variable'], styler.report_value["TE-Variable"])
        ws.write(f'I{row + 4}', self['TE-Compare'], styler.report_value["TE-Compare"])
        ws.write(f'J{row + 4}', self['TE-Value'], styler.report_value["TE-Value"])
        ws.merge_range(f'K{row + 3}:M{row + 3}', self['Expected Results (ER) - Description'], styler.report_value["Expected Results (ER) - Description"])
        ws.write(f'K{row + 4}', self['ER-Variable'], styler.report_value["ER-Variable"])
        ws.write(f'L{row + 4}', self['ER-Compare'], styler.report_value["ER-Compare"])
        ws.write(f'M{row + 4}', self['ER-Value'], styler.report_value["ER-Value"])
        ws.merge_range(f'N{row + 3}:P{row + 4}', self['Test Result'], styler.report_value["Test Result"])
        ws.merge_range(f'B{row + 6}:L{row + 26}', '', styler.report_value["Test Result Graph"])
        if self.attachment:
            ws.insert_image(row + 5, 1, self.attachment, {
                'x_offset': 0,
                'y_offset': 0,
                'x_scale': 0.4,
                'y_scale': 0.4
            })
        ws.merge_range(f'M{row + 6}:P{row + 26}', self['Test Result Description'], styler.report_value['Test Result Description'])
        ws.merge_range(f'B{row + 28}:D{row + 28}', self['Test Conductor'], styler.report_value['Test Conductor'])
        ws.merge_range(f'E{row + 28}:G{row + 28}', self['Test SW'], styler.report_value['Test SW'])
        ws.merge_range(f'H{row + 28}:J{row + 28}', self['Test HW'], styler.report_value['Test HW'])
        ws.merge_range(f'K{row + 28}:M{row + 28}', self['Test Vehicle / Engine / HIL'], styler.report_value['Test Vehicle / Engine / HIL'])
        ws.merge_range(f'N{row + 28}:P{row + 28}', self['Test Environment'], styler.report_value['Test Environment'])
        ws.merge_range(f'B{row + 30}:G{row + 30}', self['Remark / Comment'], styler.report_value['Remark / Comment'])
        ws.merge_range(f'H{row + 30}:J{row + 30}', self['Measure / Log File (.dat)'], styler.report_value['Measure / Log File (.dat)'])
        ws.merge_range(f'K{row + 30}:M{row + 30}', self['MDA Configuration File (.xda)'], styler.report_value['MDA Configuration File (.xda)'])
        ws.merge_range(f'N{row + 30}:P{row + 30}', self['Experiment File (.exp)'], styler.report_value['Experiment File (.exp)'])
        for i in range(32):
            ws.set_row(i + row, 48.5 if i == 2 else 19.25)

        if not isinstance(self.workbook, Workbook):
            wb.close()
        return

if __name__ == "__main__":
    unit = UnitTestCase()
    print(unit)
    unit['Test Result'] = "PASS TEST"
    print(unit)