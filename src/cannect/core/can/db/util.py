from cannect.utils.excel import ComExcel
from cannect.core.can.db.schema.keys import CAN_DB_KEYS

from pandas import DataFrame, Index
from pathlib import Path
from typing import Union, List
import time


def refactor_db_keys(columns: Union[Index, List]) -> List:
    """
    입력된 columns에 대해 표준 CAN DB(SPEC) keys로 변환하여 반환한다.
    Excel CAN DB(SPEC)의 각 열 이름(키 값)이 표준에 부합하게 한다.
    표준 Key 값은 @CAN_DB_KEYS로 관리한다.

    :author   이제혁
    :modified 2026.04.29
    :param
        columns: Excel CAN DB(SPEC)의 키 값의 집합 또는 리스트

    :return:
        ['ECU', 'Message', 'ID', 'DLC',  ... , 'SignalRenamed']
    """
    standard_keys = []
    for key, spec in CAN_DB_KEYS.items():
        if key in columns or key.lower() in columns:
            standard_keys.append(key)
            continue
        for synonym in spec.synonyms:
            if synonym in columns:
                standard_keys.append(key)
        if not key in standard_keys:
            raise KeyError(f'Cannot find "{key}" in columns; {columns}')
    return standard_keys


def spec_excel_to_dataframe(excel_path: Union[Path, str]) -> DataFrame:
    """
    Excel CAN DB(SPEC)을 읽어 pandas DataFrame으로 변환한다.
    * Excel 응용프로그램이 미실행 상태에서 실행하는 경우 작업 후 응용프로그램을 종료한다.

    :author    이제혁
    :modified  2026.04.29
    :param
        excel_path: Excel CAN DB(SPEC)의 경로(확장자 포함)

    :return:
        * 보안 준수를 위해 최소한의 예시만 표출 (ID 비공개)

                  ECU          Message     ID  DLC  ...  SignalRenamed
        1     CGW_CCU  ABS_ESC_01_10ms  0x---  8.0  ...           None
        2     CGW_CCU  ABS_ESC_01_10ms  0x---  8.0  ...           None
        3     CGW_CCU  ABS_ESC_01_10ms  0x---  8.0  ...           None
        ...       ...              ...    ...  ...  ...            ...
        1792      EMS      EMS_LDCBMS1  0x---  8.0  ...           None
        1793      EMS      EMS_LDCBMS1  0x---  8.0  ...           None
        1794      EMS      EMS_LDCBMS1  0x---  8.0  ...           None

        [1794 rows x 39 columns]
    """
    excel_path = Path(excel_path)

    excel_handler = ComExcel(excel_path)
    dataframe = excel_handler.to_dataframe(1, dtype=object)
    dataframe.columns = refactor_db_keys(dataframe.columns)
    dataframe = dataframe[~dataframe["ECU"].isna() & (dataframe["ECU"] != "")]

    if not excel_handler.was_open:
        excel_handler.wb.Close(SaveChanges=False)
        time.sleep(1)
        excel_handler.app.Quit()
        time.sleep(1)
    return dataframe


if __name__ == "__main__":

    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    print(spec_excel_to_dataframe(r"E:\SVN\dev.bsw\hkmc.ems.bsw.docs\branches\HEPG_Ver1p1\11_ProjectManagement\CAN_Database\자체제어기_KEFICO-EMS_CANFD.xlsx"))