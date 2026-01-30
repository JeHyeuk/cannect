from pathlib import Path
from pywintypes import com_error
from typing import Union
import win32com.client as win32


class ComExcel:

    app = None
    app_close  :bool = False
    app_visible:bool = False
    def __new__(cls, *args, **kwargs):
        try:
            cls.app = win32.GetActiveObject("Excel.Application")
        except com_error:
            cls.app = win32.Dispatch("Excel.Application")
            cls.app_close = True
        cls.app_visible = False
        return super().__new__(cls)

    def __init__(self, path:Union[str, Path]):
        self.wb = wb = self.app.Workbooks.Open(path)
        self.ws = wb.ActiveSheet
        return

    # def __del__(self):
    #     if self.app_close:
    #         self.wb.Close()
    #         self.app.Quit()