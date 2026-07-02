from pandas import DataFrame
from pathlib import Path
from pywintypes import com_error
from typing import Union
import win32com.client as win32


class ComExcel:

    def __init__(self, file:Union[str, Path], **kwargs):
        try:
            self.app = win32.GetActiveObject("Excel.Application")
            self.was_open = True
        except com_error:
            self.app = win32.Dispatch("Excel.Application")
            self.app.Visible = kwargs.get('visible', False)
            self.was_open = False

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

    def from_dataframe(self, n_sheet: int, df: DataFrame, start_row: int = 1, start_col: int = 1):
        """
        데이터프레임의 index와 column을 제외한 순수 데이터만 지정한 시트에 붙여넣습니다.

        :param n_sheet: 대상 시트 번호 (1부터 시작) 또는 시트 이름
        :param df: 붙여넣을 Pandas DataFrame
        :param start_row: 붙여넣기를 시작할 엑셀 행 번호 (기본값: 1)
        :param start_col: 붙여넣기를 시작할 엑셀 열 번호 (기본값: 1)
        """
        # 1. 대상 시트 가져오기 (작성하신 __getitem__ 활용)
        sheet = self[n_sheet]

        # 2. NaN(결측치) 처리 및 2차원 리스트 변환
        # 엑셀에 NaN이 그대로 들어가면 에러가 나거나 문자열 "nan"으로 입력될 수 있으므로 None(빈 칸)으로 변환합니다.
        clean_df = df.where(df.notnull(), None)
        data = clean_df.values.tolist()

        num_rows = len(data)
        if num_rows == 0:
            return  # 데이터가 비어있으면 종료
        num_cols = len(data[0])

        # 3. 데이터를 붙여넣을 엑셀 범위(Range) 계산
        # 엑셀은 1부터 시작하는 인덱스를 사용합니다.
        end_row = start_row + num_rows - 1
        end_col = start_col + num_cols - 1

        # 4. 범위 지정 후 데이터 한 번에 쓰기 (속도가 매우 빠름)
        excel_range = sheet.Range(
            sheet.Cells(start_row, start_col),
            sheet.Cells(end_row, end_col)
        )
        excel_range.Value = data
        return

    def save_as(self, new_file: Union[str, Path]):
        """
        현재 열려 있는 워크북을 새로운 절대 경로로 저장합니다.

        :param new_file: 저장할 새로운 파일의 절대 경로 (문자열 또는 Path 객체)
        """
        # 1. Path 객체이든 문자열이든 상관없이 절대 경로 문자열로 변환합니다.
        absolute_path = str(Path(new_file).resolve())

        # 2. 다른 이름으로 저장 실행
        # (이미 __init__에서 DisplayAlerts = False로 설정했기 때문에,
        #  동일한 이름의 파일이 있어도 묻지 않고 덮어씁니다.)
        self.wb.SaveAs(absolute_path)
        return

    def to_dataframe(self, sheet, **kwargs) -> DataFrame:
        if isinstance(sheet, int):
            data = self[sheet].UsedRange.Value
        else:
            data = sheet.UsedRange.Value
        return DataFrame(
            data=data[1:],
            columns=data[0],
            index=[n for n in range(1, len(data))],
            dtype=kwargs.get('dtype', None)
        )



if __name__ == "__main__":
    xl = ComExcel(r'E:\SVN\GSL_Build\2_BuildEnvironment\8_VTC_Environment\01_KEFICO\Rename-gtx2kefico-master.xlsx')