from cannect.schema.datadictionary import DataDictionary
from cannect.core.ir.ir import IntegrationRequest
from cannect.utils.ppt import PptRW
import pandas as pd
import pygetwindow as gw
import pyautogui as gui
import time


class ChangeHistoryManager(PptRW):

    def __init__(self, ir:IntegrationRequest, **kwargs):
        super().__init__(ir.sc.src.ppt.src, **kwargs)
        self.ir = ir

        # PAGE MODEL DETAILS
        self._set_model_slides()

        # PAGE OVERVIEW: SET FUNCTION LIST
        self.set_text_in_table(n_slide=1, n_table=2, cell=(3, 2), text=", ".join(ir.data["FunctionName"]), pos='new')
        self.set_table_font(n_slide=1, n_table=2, cell=(3, 2), size=10)

        # PAGE MODEL DESCRIPTION:
        text = DataDictionary(prev='', curr='')
        cals = []
        for md in ir.data.index:
            p_rev = ir.sc.svn[md].model.rev
            if not p_rev:
                p_rev = '-'
            c_rev = ir.data.loc[md, "SCMRev"]
            if pd.isna(c_rev) or not c_rev:
                c_rev = f'{{--{md}--}}'

            text.prev += f'%{md} <r.{p_rev}>\x0b\x0b\n'
            text.curr += f'%{md} <r.{c_rev}>\x0b-\x0b\n'


            slides = self.get_slide_n(f'{md} ')
            for slide in slides:
                self.replace_text_in_table(
                    n_slide=slide,
                    n_table=1,
                    cell=(1, 1),
                    prev="Rev.",
                    post=f"Rev.{p_rev}"
                )

                self.replace_text_in_table(
                    n_slide=slide,
                    n_table=1,
                    cell=(1, 2),
                    prev="Rev.",
                    post=f"Rev.{c_rev}"
                )

            slides = self.get_slide_n(f'{md} / Element')
            for slide in slides:
                self.set_text_in_table(
                    n_slide=slide,
                    n_table=1,
                    cell=(3, 1),
                    text='Element 삭제\x0b' + str(ir.data.loc[md, "ElementDeleted"]),
                    pos="new"
                )
                self.set_text_in_table(
                    n_slide=slide,
                    n_table=1,
                    cell=(3, 2),
                    text='Element 추가\x0b' + str(ir.data.loc[md, "ElementAdded"]),
                    pos="new"
                )

            if 'param' in ir.inst[md]:
                cals.append(ir.inst[md].param)
        self.set_text_in_table(n_slide=2, n_table=1, cell=(2, 1), text=text.prev[:-1], pos='new')
        self.set_text_in_table(n_slide=2, n_table=1, cell=(2, 2), text=text.curr[:-1], pos='new')

        # WRITE CALIBRATION GUIDE
        if len(cals) == 0:
            return

        n_param = self.get_slide_n('Calibration')[0]
        for n in range(len(cals) - 1):
            self.ppt.Slides(n_param).Duplicate()

        for n, param in enumerate(cals):
            table = self._get_table(n_param + n, 1)
            if len(param) > 3:
                for _ in range(len(param) - 3):
                    table.Rows.Add()

            for r, index in enumerate(param.index, start=1):
                row = param.loc[index]
                for c, val in enumerate(row.values, start=1):
                    cell = table.Cell(r + 1, c).Shape
                    cell.TextFrame.TextRange.Text = str(val)
                    cell.TextFrame.TextRange.Font.Name = "현대산스 Text"
                    cell.TextFrame.TextRange.Font.Size = 9

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
            self.set_text_in_table(n_slide=n_regulation[0], n_table=2, cell=(1, 2), text=title, pos='new')
        n_checklist = self.get_slide_n('SW변경내역서 Check List')
        if n_checklist:
            self.set_text_in_table(n_slide=n_checklist[0], n_table=2, cell=(1, 2), text=title, pos='new')

    @property
    def developer(self) -> str:
        return self.__dict__.get('_developer', '')

    @developer.setter
    def developer(self, developer:str):
        self.__dict__['_developer'] = developer
        self.set_text_in_table(n_slide=1, n_table=1, cell=(2, 1), text=developer, pos='new')
        self.set_table_font(n_slide=1, n_table=1, cell=(2, 1), size=10)
        user = f'현대케피코\n{developer}'
        n_checklist = self.get_slide_n('SW변경내역서 Check List')
        if n_checklist:
            self.set_text_in_table(n_slide=n_checklist[2], n_table=1, cell=(16, 5), text=user, pos='new')

    @property
    def issue(self) -> str:
        return self.__dict__.get('_issue', '')

    @issue.setter
    def issue(self, issue:str):
        self.__dict__['_issue'] = issue
        self.set_table_font(n_slide=1, n_table=2, cell=(3, 8), name="현대산스 Text")
        self.set_text_in_table(n_slide=1, n_table=2, cell=(3, 8), text=issue, pos='new')

    @property
    def lcr(self) -> str:
        return self.__dict__.get('_lcr', '')

    @property
    def lcr_submit_team(self) -> str:
        return self.__dict__.get('_lcr_submit_team', '')

    @property
    def lcr_submitter(self) -> str:
        return self.__dict__.get('_lcr_submitter', '')

    @lcr.setter
    def lcr(self, lcr:str):
        if not lcr:
            return
        self.__dict__['_lcr'] = lcr

        self.set_text_in_table(n_slide=1, n_table=2, cell=(4, 8), text=lcr, pos='before')
        if self.lcr_submit_team == self.lcr_submitter == '':
            text = f'(필수 항목) LCR 번호, LCR 제기팀 및 담당자 기재 要'
        else:
            text = f'{self.lcr_submit_team} / {self.lcr_submitter}'
        self.set_text_in_table(n_slide=1, n_table=2, cell=(4, 8), text=text, pos='after')

        n_regulation = self.get_slide_n('법규 정합성')
        if n_regulation:
            self.set_text_in_table(n_slide=n_regulation[0], n_table=2, cell=(1, 4), text=lcr, pos='new')
        n_checklist = self.get_slide_n('SW변경내역서 Check List')
        if n_checklist:
            self.set_text_in_table(n_slide=n_checklist[0], n_table=2, cell=(1, 4), text=lcr, pos='new')

    @lcr_submit_team.setter
    def lcr_submit_team(self, team:str):
        self.__dict__['_lcr_submit_team'] = team

    @lcr_submitter.setter
    def lcr_submitter(self, submitter:str):
        self.__dict__['_lcr_submitter'] = submitter

    @property
    def problem(self) -> str:
        return self.__dict__.get('_problem', '')

    @problem.setter
    def problem(self, problem:str):
        if not problem:
            return
        self.set_text_in_table(n_slide=1, n_table=2, cell=(5, 1), text=problem, pos='new')

    @property
    def cause_requirement(self) -> str:
        return self.__dict__.get('_cause_requirement', '')

    @cause_requirement.setter
    def cause_requirement(self, cause_requirement:str):
        self.set_text_in_table(n_slide=1, n_table=3, cell=(1, 1), text=cause_requirement, pos='new')

    def _set_model_slides(self):
        self.set_shape(n_slide=3, n_shape=1, width=26.1 * 28.346, left=0.8 * 28.346)
        self.set_text_font(n_slide=3, n_shape=1, name="현대산스 Text", size=20)
        self.set_table_height(n_slide=3, n_table=1, row=2, height=9 * 28.346)
        self.set_table_height(n_slide=3, n_table=1, row=3, height=5.5 * 28.346)
        self.set_table_text_align(n_slide=3, n_table=1, cell=(3, 1))
        self.set_table_text_align(n_slide=3, n_table=1, cell=(3, 2))
        self.set_table_font(n_slide=3, n_table=1, cell=(3, 1), size=12)
        self.set_table_font(n_slide=3, n_table=1, cell=(3, 2), size=12)
        for n in range(3 * len(self.ir) - 1):
            self.ppt.Slides(3).Duplicate()
        
        # if self.ppt.SectionProperties.Count == 0:
        #     self.ppt.SectionProperties.AddSection(1, f'기본 구역')
        for n, model in enumerate(self.ir.data.index, start=1):
            n_default = 3 * (n - 1) + 3
            n_element = 3 * (n - 1) + 4
            n_formula = 3 * (n - 1) + 5
            self.ppt.SectionProperties.AddBeforeSlide(n_default, f'%{model}')
            self.set_text(n_slide=n_default, n_shape=1, text=f'SW 변경 내용 상세: %{model} /', pos='new')
            self.set_text(n_slide=n_element, n_shape=1, text=f'SW 변경 내용 상세: %{model} / Element', pos='new')
            self.set_text(n_slide=n_formula, n_shape=1, text=f'SW 변경 내용 상세: %{model} / Implementation', pos='new')
            self.set_text_in_table(n_slide=n_element, n_table=1, cell=(3, 1), text="Element 삭제\x0b", pos="new")
            self.set_text_in_table(n_slide=n_element, n_table=1, cell=(3, 2), text="Element 추가\x0b", pos="new")
            self.set_text_in_table(n_slide=n_formula, n_table=1, cell=(3, 1), text="Impl. 삭제\x0b", pos="new")
            self.set_text_in_table(n_slide=n_formula, n_table=1, cell=(3, 2), text="Impl. 추가\x0b", pos="new")
        self.ppt.SectionProperties.AddBeforeSlide(self.get_slide_n('Calibration')[0], 'Calibration Guide')
        return
