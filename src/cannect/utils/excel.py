from pandas import DataFrame
from pathlib import Path
from pywintypes import com_error
from typing import Union
import win32com.client as win32


class ComExcel:

    def __init__(self, file:Union[str, Path], **kwargs):
        try:
            self.app = win32.GetActiveObject("Excel.Application")
            self.close_end = False
        except com_error:
            self.app = win32.Dispatch("Excel.Application")
            self.app.Visible = kwargs.get('visible', False)
            self.close_end = True

        if hasattr(self.app, 'DisplayAlerts'):
            self.app.DisplayAlerts = False

        self.wb = wb = self.app.Workbooks.Open(file)
        self.ws = wb.ActiveSheet
        return

    def __iter__(self):
        for sheet in self.wb.Sheets:
            yield sheet

    def __len__(self) -> int:
        return self.wb.Sheets.Count

    def __getitem__(self, n_sheet:int):
        return self.wb.Sheets(n_sheet)

    def close(self):
        self.wb.Close(False)
        return

    def to_dataframe(self, sheet) -> DataFrame:
        if isinstance(sheet, int):
            data = self[sheet].UsedRange.Value
        else:
            data = sheet.UsedRange.Value
        return DataFrame(data[1:], columns=data[0], index=[n for n in range(2, len(data) + 1)])



if __name__ == "__main__":
    xl = ComExcel(r'E:\SVN\GSL_Build\2_BuildEnvironment\8_VTC_Environment\01_KEFICO\Rename-gtx2kefico-master.xlsx')