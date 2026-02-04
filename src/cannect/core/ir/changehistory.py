from cannect.core.ir.ir import IntegrationRequest
from cannect.utils.ppt import PptRW
from cannect.utils import tools
from pandas import DataFrame
from typing import Iterable, List
import pygetwindow as gw
import pyautogui as gui
import time


class ChangeHistoryManager(PptRW):

    def __init__(self, ir:IntegrationRequest):
        ir.logger.log(f'[WRITE PPT ON "{tools.path_abbreviate(ir.deliverables.change_history)}"]')
        if not ir.is_previous_svn_version_selected():
            ir.logger.log('! WARNING: PREVIOUS MODEL NOT SELECTED')

        super().__init__(ir.deliverables.change_history)
        self.ir = ir

        ir.logger.log('>>> RESIZING COVER PAGE')
        self._resize_cover()

        # PAGE OVERVIEW: SET FUNCTION LIST
        self.set_text_in_table(n_slide=1, n_table=2, cell=(3, 2), text=", ".join(ir.table["FunctionName"]), pos='new')
        self.set_table_font(n_slide=1, n_table=2, cell=(3, 2), size=10)

        # PAGE MODEL DESCRIPTION:
        if ir.is_previous_svn_version_selected():
            ir.logger.log('>>> WRITE ON "SW 기능 상세 설명 - 변경 전"')
            text = ''
            for n in ir.p_table.index:
                text += f'%{ir.p_table.loc[n, "FunctionName"]} <r.{ir.p_table.loc[n, "SCMRev"]}>\x0b\x0b\n'
            text = text[:-1]
            self.set_text_in_table(n_slide=2, n_table=1, cell=(2, 1), text=text, pos='new')

        ir.logger.log('>>> WRITE ON "SW 기능 상세 설명 - 변경 후"')
        text = ''
        for n in ir.table.index:
            text += f'%{ir.table.loc[n, "FunctionName"]} <r.{ir.table.loc[n, "SCMRev"]}>\x0b-\x0b\n'
        text = text[:-1]
        self.set_text_in_table(n_slide=2, n_table=1, cell=(2, 2), text=text, pos='new')

        # PAGE MODEL DETAILS
        ir.logger.log('>>> GENERATE SLIDES ')
        self._set_model_slides()

        if ir.is_previous_svn_version_selected():
            ir.logger('>>> WRITING PREVIOUS MODEL DETAILS...')
            for n in ir.p_table.index:
                name, rev = ir.p_table.loc[n, "FunctionName"], ir.p_table.loc[n, "SCMRev"]
                ir.logger(f'>>> ... {name} @{rev}')
                slides = self.get_slide_n(f'{name} ')
                for slide in slides:
                    self.replace_text_in_table(
                        n_slide=slide,
                        n_table=1,
                        cell=(1, 1),
                        prev="Rev.",
                        post=f"Rev.{rev}"
                    )

        ir.logger('>>> WRITING REVISED MODEL DETAILS...')
        for n in ir.table.index:
            name, rev = ir.table.loc[n, "FunctionName"], ir.table.loc[n, "SCMRev"]
            ir.logger(f'>>> ... {name} @{rev}')
            slides = self.get_slide_n(f'{name} ')
            for slide in slides:
                self.replace_text_in_table(
                    n_slide=slide,
                    n_table=1,
                    cell=(1, 2),
                    prev="Rev.",
                    post=f"Rev.{rev}"
                )
            slides = self.get_slide_n(f'{name} / Element')
            for slide in slides:
                self.set_text_in_table(
                    n_slide=slide,
                    n_table=1,
                    cell=(3, 1),
                    text='Element 삭제\x0b' + ir.table.loc[n, "ElementDeleted"],
                    pos="new"
                )
                self.set_text_in_table(
                    n_slide=slide,
                    n_table=1,
                    cell=(3, 2),
                    text='Element 추가\x0b' + ir.table.loc[n, "ElementAdded"],
                    pos="new"
                )

        # WRITE CALIBRATION GUIDE
        if len(ir.parameters) == 0:
            return

        ir.logger('>>> WRITING CALIBRATION PARAMETERS')

        n_param = self.get_slide_n('Calibration')[0]
        for n in range(len(ir.parameters) - 1):
            self.ppt.Slides(n_param).Duplicate()

        for n, param in enumerate(ir.parameters):
            table = self._get_table(n_param + n, 1)
            if len(param) > 3:
                for _ in range(len(param) - 3):
                    table.Rows.Add()
            table.Columns(1).Width = 5.0 * 28.346
            table.Columns(2).Width = 7.0 * 28.346
            table.Columns(3).Width = 4.0 * 28.346
            table.Columns(5).Width = 2.0 * 28.346
            table.Columns(6).Width = 2.0 * 28.346
            table.Columns(7).Width = 2.0 * 28.346
            for r, index in enumerate(param.index, start=1):
                row = param.loc[index]
                for c, val in enumerate(row.values, start=1):
                    cell = table.Cell(r + 1, c).Shape
                    cell.TextFrame.TextRange.Text = str(val)
                    cell.TextFrame.TextRange.Font.Name = "현대하모니 L"
                    cell.TextFrame.TextRange.Font.Size = 10

                    cell.TextFrame.TextRange.ParagraphFormat.Alignment = 1 if c == 2 else 2
                    cell.TextFrame.VerticalAnchor = 3
        return

    @classmethod
    def routine_capture(cls, ppt:str='', size:int=26, *hotkey):
        """
        최초 픽픽 또는 기타 툴로 최초 캡쳐가 되어 있어야 함.
        반복 캡쳐는 단축키로 수행이 가능해야 함
        @param ppt  : 변경내역서 파일명
        @param size :
        """
        windows = gw.getAllTitles()
        ascet_diff = None
        pptx = []
        for title in windows:
            if title and title == "ASCET-DIFF":
                ascet_diff = title
            if title and '.pptx' in title:
                pptx.append(title)

        if ascet_diff is None:
            raise OSError('ASCET-DIFF 를 찾을 수 없습니다')
        if not pptx:
            raise OSError('변경내역서를 찾을 수 없습니다')
        if len(pptx) >= 2 and not ppt:
            raise OSError('열려있는 pptx가 2개 이상이며 변경내역서를 특정할 수 없습니다. @ppt = ""')
        pptx = [_ppt for _ppt in pptx if _ppt.startswith(ppt)][0]

        window = gw.getWindowsWithTitle(ascet_diff)[0]
        window.activate()

        if not hotkey:
            hotkey = 'shift', 'ctrl', 'd'
        gui.hotkey(*hotkey)
        time.sleep(0.5)

        report = gw.getWindowsWithTitle(pptx)[0]
        report.activate()
        gui.hotkey('ctrl', 'v')
        time.sleep(0.5)

        gui.hotkey('alt', '6')
        time.sleep(0.2)

        gui.write(str(size))
        gui.press('enter')
        time.sleep(0.2)

        return

    def _resize_cover(self):
        """
        | n ==  7 | n == 3 |
        | n ==  8 | n == 4 |
        | n ==  9 | n == 5 |
        | n == 10 | n == 6 |
        :return:
        """
        for n, shape in enumerate(self.ppt.Slides.Item(1).Shapes, start=1):
            if shape.HasTable:
                if n in [7, 8, 9, 10]:
                    shape.Left = 0.76 * 28.346
                    shape.Top = {7:2.77, 8:8.1, 9:11.86, 10:15.53}[n] * 28.346
                if n in [3, 4, 5, 6]:
                    shape.Width = 22.4 * 28.346
                    shape.Left = 4.36 * 28.346
                    shape.Top = {3: 2.77, 4: 8.1, 5: 11.86, 6: 15.53}[n] * 28.346
                    if n == 3:
                        shape.Table.Rows(5).Height = 1.69 * 28.346
                    else:
                        shape.Height = {4:3.6, 5:3.5, 6:2.36}[n] * 28.346


    @property
    def title(self) -> str:
        return self.__dict__.get('_title', '')

    @title.setter
    def title(self, title:str):
        self.__dict__['_title'] = title
        self.set_text(n_slide=1, n_shape=1, text=title, pos='new')
        self.set_text_font(n_slide=1, n_shape=1, size=24)
        n_regulation = self.get_slide_n('법규 정합성')
        if n_regulation:
            self.set_text_in_table(n_slide=n_regulation[0], n_table=1, cell=(1, 2), text=title, pos='new')
        n_checklist = self.get_slide_n('SW변경내역서 Check List')
        if n_checklist:
            self.set_text_in_table(n_slide=n_checklist[0], n_table=1, cell=(1, 2), text=title, pos='new')

    @property
    def developer(self) -> str:
        return self.__dict__.get('_developer', '')

    @developer.setter
    def developer(self, developer:str):
        self.__dict__['_developer'] = developer
        self.set_text_in_table(n_slide=1, n_table=1, cell=(2, 1), text=developer, pos='new')
        self.set_table_font(n_slide=1, n_table=1, cell=(2, 1), size=10)

    @property
    def issue(self) -> str:
        return self.__dict__.get('_issue', '')

    @issue.setter
    def issue(self, issue:str):
        self.__dict__['_issue'] = issue
        self.set_table_font(n_slide=1, n_table=2, cell=(3, 8), name="현대하모니 L")
        self.set_text_in_table(n_slide=1, n_table=2, cell=(3, 8), text=issue, pos='new')

    @property
    def lcr(self) -> str:
        return self.__dict__.get('_lcr', '')

    @lcr.setter
    def lcr(self, lcr:str):
        self.__dict__['_lcr'] = lcr
        self.set_text_in_table(n_slide=1, n_table=2, cell=(4, 8), text=lcr, pos='before')
        n_regulation = self.get_slide_n('법규 정합성')
        if n_regulation:
            self.set_text_in_table(n_slide=n_regulation[0], n_table=1, cell=(1, 4), text=lcr, pos='new')
        n_checklist = self.get_slide_n('SW변경내역서 Check List')
        if n_checklist:
            self.set_text_in_table(n_slide=n_checklist[0], n_table=1, cell=(1, 4), text=lcr, pos='new')

    @property
    def problem(self) -> str:
        return self.__dict__.get('_problem', '')

    @problem.setter
    def problem(self, problem:str):
        self.set_text_in_table(n_slide=1, n_table=2, cell=(5, 1), text=problem, pos='new')

    def _set_model_slides(self):
        ir = self.ir.table
        self.set_shape(n_slide=3, n_shape=1, width=26.1 * 28.346, left=0.8 * 28.346)
        self.set_text_font(n_slide=3, n_shape=1, name="현대하모니 M", size=20)
        self.set_table_height(n_slide=3, n_table=1, row=2, height=11 * 28.346)
        self.set_table_height(n_slide=3, n_table=1, row=3, height=3 * 28.346)
        self.set_table_text_align(n_slide=3, n_table=1, cell=(3, 1))
        self.set_table_text_align(n_slide=3, n_table=1, cell=(3, 2))
        self.set_table_font(n_slide=3, n_table=1, cell=(3, 1), size=12)
        self.set_table_font(n_slide=3, n_table=1, cell=(3, 2), size=12)
        for n in range(3 * len(ir) - 1):
            self.ppt.Slides(3).Duplicate()
        
        # if self.ppt.SectionProperties.Count == 0:
        #     self.ppt.SectionProperties.AddSection(1, f'기본 구역')
        for n, i in enumerate(ir.index, start=1):
            n_default = 3 * i + 3
            n_element = 3 * i + 4
            n_formula = 3 * i + 5
            name = ir.loc[i]["FunctionName"]
            self.ppt.SectionProperties.AddBeforeSlide(n_default, f'%{name}')
            self.set_text(n_slide=n_default, n_shape=1, text=f'SW 변경 내용 상세: %{name} /', pos='new')
            self.set_text(n_slide=n_element, n_shape=1, text=f'SW 변경 내용 상세: %{name} / Element', pos='new')
            self.set_text(n_slide=n_formula, n_shape=1, text=f'SW 변경 내용 상세: %{name} / Implementation', pos='new')
            self.set_text_in_table(n_slide=n_element, n_table=1, cell=(3, 1), text="Element 삭제\x0b", pos="new")
            self.set_text_in_table(n_slide=n_element, n_table=1, cell=(3, 2), text="Element 추가\x0b", pos="new")
            self.set_text_in_table(n_slide=n_formula, n_table=1, cell=(3, 1), text="Impl. 삭제\x0b", pos="new")
            self.set_text_in_table(n_slide=n_formula, n_table=1, cell=(3, 2), text="Impl. 추가\x0b", pos="new")
        self.ppt.SectionProperties.AddBeforeSlide(self.get_slide_n('Calibration')[0], 'Calibration Guide')
        return
