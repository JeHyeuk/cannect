from cannect.config import env
from cannect.core.testcase.unitcase import UnitTestCase
from cannect.core.testcase.style import Style
from datetime import datetime
from pandas import DataFrame, ExcelWriter
from typing import Dict, List, Hashable, Union
import xlsxwriter as xlsx
import os


class TestCase:

    def __init__(self, *args:UnitTestCase):
        self._units: List[UnitTestCase] = []
        self._template: str = env.SVN_CAN / "CAN_TestCase/TESTCASE_TEMPLATE.xlsm"
        self._filename: str = f'TESTCASE @{str(datetime.now()).replace(" ", "_").replace(":", ";").split(".")[0]}'
        self._data = ""
        self._mdf = None
        for arg in args:
            self._units.append(arg)
        return

    def __repr__(self):
        return repr(self.cases)

    def __len__(self) -> int:
        return len(self._units)

    def __iter__(self):
        for unit in self._units:
            yield unit

    def __getitem__(self, item: Union[int, str]) -> UnitTestCase:
        if isinstance(item, int):
            return self._units[item - 1]
        elif isinstance(item, str):
            for unit in self._units:
                if unit["Test Case - ID"] == item:
                    return unit
        raise KeyError

    def __setitem__(self, key: str, value):
        for unit in self._units:
            if not key in unit.index:
                raise KeyError(f'Unknown key: {key}')
            unit[key] = value
        return

    @property
    def data(self) -> str:
        return self._data

    @data.setter
    def data(self, data:str):
        from pyems.mdf import MdfReader
        self._data = data
        self._mdf = MdfReader(data)
        self["Measure / Log File (.dat)"] = os.path.basename(data)
        return

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = filename

    @property
    def directory(self) -> str:
        return str(env.DOWNLOADS / self.filename)

    @property
    def cases(self) -> DataFrame:
        return DataFrame(self._units)

    def append(self, case: UnitTestCase):
        self._units.append(case)
        return

    def to_testcase(self, filename: Union[str, Hashable] = ""):
        if filename:
            self.filename = filename
        with ExcelWriter(f"{self.directory}.xlsx", engine="xlsxwriter") as writer:
            cases = self.cases.copy()
            cases.to_excel(writer, sheet_name="Test Case", index=False)

            wb, ws = writer.book, writer.sheets["Test Case"]
            styler = Style(wb, ws)
            for n, col in enumerate(cases.columns):
                ws.write(0, n, col, styler.testcase_label[col])
                for m, value in enumerate(cases[col]):
                    ws.write(m + 1, n, value, styler.testcase_value[col])

            for n, col in enumerate(cases.columns):
                lens = len(col)
                for val in cases[col]:
                    vals = val.split('\n') if '\n' in str(val) else [str(val)]
                    maxs = max([len(v) for v in vals])
                    if maxs > lens:
                        lens = maxs
                ws.set_column(n, n, lens + 2)
        return

    def to_report(self, filename: Union[str, Hashable] = ""):
        if filename:
            self.filename = filename
        file = f"{self.directory.replace('TestCase', 'TestReport')}.xlsx"
        if not "TCU" in file and not "DATC" in file and "TC" in file:
            file = file.replace("TC", "TR")

        tc = xlsx.Workbook(filename=file)
        ws = tc.add_worksheet(name="Test Report MLT")
        ws.set_column('A:A', 1.63)
        styler = Style(tc, ws)
        styler.adjust_width()
        for n, testcase in enumerate(self):
            testcase.workbook = tc
            testcase.to_report(1 + (n * 32))
        tc.close()
        return

    def to_labfile(self, name: Union[str, Hashable] = ""):
        filename = name if name else self.filename.replace("TESTCASE", "LABFILE")
        if not filename.endswith(".lab"):
            filename += ".lab"
        file = env.DOWNLOADS / filename

        elem, param = list(), list()
        for _case in self._units:
            for var in _case.variable:
                box = param if var.endswith("_C") else elem
                if not var in box:
                    box.append(var)
        EOL = "\n"
        with open(file, "w", encoding="utf-8") as f:
            f.write(f"""[SETTINGS]
    Version;V1.1


    [RAMCELL]
    {EOL.join(sorted(elem))}


    [LABEL]
    {EOL.join(sorted(param))}
    """)
        return

    def to_clipboard(self):
        self.cases.to_clipboard(index=False)
        return




if __name__ == "__main__":
    from emscan.core.testcase.unitcase import UnitTestCase
    tc = TestCase(UnitTestCase())
    tc.to_report()