from xlsxwriter import Workbook
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet


class Style:

    _testcase_label = {
        "NO": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "Category": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Group": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Test Case - ID": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Test Case Name": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Requirement - Traceability": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 5,
            "bottom": 5
        },
        "Test Purpose, Description": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#DAEEF3',
            "top": 5,
            "left": 5,
            "right": 5,
            "bottom": 5
        },
        "PreCondition (PC) - Description": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#FDE9D9',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "PC-Variable": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#FDE9D9',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "PC-Compare": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#FDE9D9',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "PC-Value": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#FDE9D9',
            "top": 5,
            "left": 1,
            "right": 5,
            "bottom": 5
        },
        "Test Execution (TE) - Description": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#E4DFEC',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "TE-Variable": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#E4DFEC',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "TE-Compare": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#E4DFEC',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "TE-Value": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#E4DFEC',
            "top": 5,
            "left": 1,
            "right": 5,
            "bottom": 5
        },
        "Expected Results (ER) - Description": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#DCE6F1',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "ER-Variable": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#DCE6F1',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "ER-Compare": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "text_wrap": True,
            "bg_color": '#DCE6F1',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "ER-Value": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#DCE6F1',
            "top": 5,
            "left": 5,
            "right": 5,
            "bottom": 5
        },
        "Test Result": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#F2DCDB',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "Test Result Description": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#F2DCDB',
            "top": 5,
            "left": 1,
            "right": 5,
            "bottom": 5
        },
        "Test Conductor": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "Test SW": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Test HW": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Test Vehicle / Engine / HIL": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Test Environment": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#EBF1DE',
            "top": 5,
            "left": 1,
            "right": 5,
            "bottom": 5
        },
        "Remark / Comment": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#DAEEF3',
            "top": 5,
            "left": 5,
            "right": 5,
            "bottom": 5
        },
        "Measure / Log File (.dat)": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#D9D9D9',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "MDA Configuration File (.xda)": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#D9D9D9',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "Experiment File (.exp)": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#D9D9D9',
            "top": 5,
            "left": 1,
            "right": 5,
            "bottom": 5
        },
        "VIO": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 5,
            "right": 1,
            "bottom": 5
        },
        "SWC": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "MLT": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "SLT": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "SDT": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "FDT": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "LVR": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "DCV": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "LSL": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "PSV": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 1,
            "bottom": 5
        },
        "EOL": {
            "align": "center",
            "valign": "vcenter",
            "font_name": "Modern H Medium",
            "font_color": "black",
            "font_size": 10,
            "bold": True,
            "text_wrap": True,
            "bg_color": '#B7DEE8',
            "top": 5,
            "left": 1,
            "right": 5,
            "bottom": 5
        },
    }

    _testcase_value = {
        "align": "center",
        "valign": "vcenter",
        "font_name": "Modern H Medium",
        "font_color": "black",
        "font_size": 10,
        "text_wrap": True,
        "left": 1,
        "right": 1,
        "bottom": 1
    }
    _testcase_description = {
        "align": "left",
        "valign": "vcenter",
        "font_name": "Modern H Medium",
        "font_color": "black",
        "font_size": 10,
        "text_wrap": True,
        "left": 1,
        "right": 1,
        "bottom": 1
    }

    def __init__(self, wb:Workbook, ws:Worksheet):
        self.wb, self.ws = wb, ws
        self.rgb = lambda r, g, b: f'#{hex(r)[2:].upper()}{hex(g)[2:].upper()}{hex(b)[2:].upper()}'
        self.testcase_label = {}
        self.testcase_value = {}
        self.report_label = {}
        self.report_value = {}
        for col in self._testcase_label:
            prop = self._testcase_description.copy() if "Description" in col else self._testcase_value.copy()
            prop["bg_color"] = self._testcase_label[col]["bg_color"]
            self.testcase_label[col] = wb.add_format(self._testcase_label[col])
            self.testcase_value[col] = wb.add_format(prop)

        for col in self._testcase_label:
            prop = self._testcase_label[col].copy()
            prop["bottom"] = 1
            if col in ["Category", "Group", "Test Case - ID", "Test Case Name", "Requirement - Traceability"]:
                if col == "Category":
                    prop["left"] = 5
            if "Description" in col or col in ["Test Result"]:
                prop["left"] = prop["right"] = 1
                if col == "Test Purpose, Description":
                    prop["left"] = 5
                if col.startswith("Test Result"):
                    prop["right"] = 5
                if col == "Test Result Description":
                    prop_copy = prop.copy()
                    prop_copy["right"] = 1
                    prop_copy["left"] = 5
                    self.report_label["Test Result Graph"] = wb.add_format(prop_copy)
            if col == "Remark / Comment":
                prop["top"] = prop["right"] = 1
            if col in ["Measure / Log File (.dat)", "MDA Configuration File (.xda)", "Experiment File (.exp)"]:
                prop["top"] = 1
                if col == "Measure / Log File (.dat)":
                    prop["left"] = 1
            self.report_label[col] = wb.add_format(prop)

        for col in self._testcase_label:
            prop = self._testcase_description.copy() if "Description" in col else self._testcase_value.copy()
            if col in ["Category", "Group", "Test Case - ID", "Test Case Name", "Requirement - Traceability",
                       "Remark / Comment", "Measure / Log File (.dat)", "MDA Configuration File (.xda)",
                       "Experiment File (.exp)"]:
                prop["bottom"] = 5
            if "Description" in col and (not "Condition" in col):
                prop["valign"] = "top"
            if col in ["Category", "Test Purpose, Description", "Test Conductor", "Remark / Comment"]:
                prop["left"] = 5
            if col in ["Requirement - Traceability", "Test Result", "Test Result Description", "Test Environment",
                       "Experiment File (.exp)"]:
                prop["right"] = 5
            if col == "Test Result":
                prop_copy = prop.copy()
                prop_copy["right"] = 1
                prop_copy["left"] = 5
                self.report_value["Test Result Graph"] = wb.add_format(prop_copy)

            self.report_value[col] = wb.add_format(prop)

        return

    def adjust_width(self):
        self.ws.set_column('A:A', 1.63)
        for col in ["C", "F", "I", "L", "O"]:
            self.ws.set_column(f'{col}:{col}', 3.13)
        for col in ["B", "D", "E", "G", "H", "J", "K", "M", "N", "P"]:
            self.ws.set_column(f'{col}:{col}', 13)
        return

    @property
    def data(self) -> Format:
        if not hasattr(self, "_format_data"):
            self.__setattr__(
                "_format_data",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    # 'border': 1,
                    'border_color': '#000000'
                })
            )
        return self.__getattribute__("_format_data")

    @property
    def desc(self) -> Format:
        if not hasattr(self, "_format_desc"):
            self.__setattr__(
                "_format_desc",
                self.wb.add_format({
                    'align': 'left',
                    'valign': 'top',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    # 'border': 1,
                    'border_color': '#000000'
                })
            )
        return self.__getattribute__("_format_desc")

    @property
    def desc2(self) -> Format:
        if not hasattr(self, "_format_desc2"):
            self.__setattr__(
                "_format_desc2",
                self.wb.add_format({
                    'align': 'left',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    # 'border': 1,
                    'border_color': '#000000'
                })
            )
        return self.__getattribute__("_format_desc2")

    @property
    def label_meta(self) -> Format:
        if not hasattr(self, "_format_meta"):
            self.__setattr__(
                "_format_meta",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(235, 241, 222)
                })
            )
        return self.__getattribute__("_format_meta")

    @property
    def label_purpose(self) -> Format:
        if not hasattr(self, "_format_purp"):
            self.__setattr__(
                "_format_purp",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(218, 238, 243)
                })
            )
        return self.__getattribute__("_format_purp")

    @property
    def label_condition(self) -> Format:
        if not hasattr(self, "_format_cond"):
            self.__setattr__(
                "_format_cond",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(253, 233, 217)
                })
            )
        return self.__getattribute__("_format_cond")

    @property
    def label_execution(self) -> Format:
        if not hasattr(self, "_format_exec"):
            self.__setattr__(
                "_format_exec",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(228, 223, 236)
                })
            )
        return self.__getattribute__("_format_exec")

    @property
    def label_expectation(self) -> Format:
        if not hasattr(self, "_format_expect"):
            self.__setattr__(
                "_format_expect",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(220, 230, 241)
                })
            )
        return self.__getattribute__("_format_expect")

    @property
    def label_result(self) -> Format:
        if not hasattr(self, "_format_res"):
            self.__setattr__(
                "_format_res",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(242, 220, 219)
                })
            )
        return self.__getattribute__("_format_res")

    @property
    def label_comment(self) -> Format:
        if not hasattr(self, "_format_comm"):
            self.__setattr__(
                "_format_comm",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(218, 238, 243)
                })
            )
        return self.__getattribute__("_format_comm")

    @property
    def label_resource(self) -> Format:
        if not hasattr(self, "_format_src"):
            self.__setattr__(
                "_format_src",
                self.wb.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'font_name': 'Modern H Medium',
                    'font_color': 'black',
                    'font_size': 10,
                    'text_wrap': True,
                    'bold': True,
                    # 'border': 1,
                    'border_color': '#000000',
                    'bg_color': self.rgb(217, 217, 217)
                })
            )
        return self.__getattribute__("_format_src")

    @property
    def label(self) -> dict:
        return {
            "NO": self.label_meta,
            "Category": self.label_meta,
            "Group": self.label_meta,
            "Test Case - ID": self.label_meta,
            "Test Case Name": self.label_meta,
            "Requirement - Traceability": self.label_meta,
            "Test Purpose, Description": self.label_purpose,
            "PreCondition (PC) - Description": self.label_condition,
            "PC-Variable": self.label_condition,
            "PC-Compare": self.label_condition,
            "PC-Value": self.label_condition,
            "Test Execution (TE) - Description": self.label_execution,
            "TE-Variable": self.label_execution,
            "TE-Compare": self.label_execution,
            "TE-Value": self.label_execution,
            "Expected Results (ER) - Description": self.label_expectation,
            "ER-Variable": self.label_expectation,
            "ER-Compare": self.label_expectation,
            "ER-Value": self.label_expectation,
            "Test Result": self.label_result,
            "Test Result Description": self.label_result,
            "Test Conductor": self.label_meta,
            "Test SW": self.label_meta,
            "Test HW": self.label_meta,
            "Test Vehicle / Engine / HIL": self.label_meta,
            "Test Environment": self.label_meta,
            "Remark / Comment": self.label_comment,
            "Measure / Log File (.dat)": self.label_resource,
            "MDA Configuration File (.xda)": self.label_resource,
            "Experiment File (.exp)": self.label_resource,
            "VIO": self.data,
            "SWC": self.data,
            "MLT": self.data,
            "SLT": self.data,
            "SDT": self.data,
            "FDT": self.data,
            "LVR": self.data,
            "DCV": self.data,
            "LSL": self.data,
            "PSV": self.data,
            "EOL": self.data,
        }

    @property
    def content(self) -> dict:
        return {
            "NO": self.data,
            "Category": self.data,
            "Group": self.data,
            "Test Case - ID": self.data,
            "Test Case Name": self.desc2,
            "Requirement - Traceability": self.data,
            "Test Purpose, Description": self.desc2,
            "PreCondition (PC) - Description": self.data,
            "PC-Variable": self.data,
            "PC-Compare": self.data,
            "PC-Value": self.data,
            "Test Execution (TE) - Description": self.desc2,
            "TE-Variable": self.data,
            "TE-Compare": self.data,
            "TE-Value": self.data,
            "Expected Results (ER) - Description": self.desc2,
            "ER-Variable": self.data,
            "ER-Compare": self.data,
            "ER-Value": self.data,
            "Test Result": self.data,
            "Test Result Description": self.desc2,
            "Test Conductor": self.data,
            "Test SW": self.data,
            "Test HW": self.data,
            "Test Vehicle / Engine / HIL": self.data,
            "Test Environment": self.data,
            "Remark / Comment": self.data,
            "Measure / Log File (.dat)": self.data,
            "MDA Configuration File (.xda)": self.data,
            "Experiment File (.exp)": self.data,
            "VIO": self.data,
            "SWC": self.data,
            "MLT": self.data,
            "SLT": self.data,
            "SDT": self.data,
            "FDT": self.data,
            "LVR": self.data,
            "DCV": self.data,
            "LSL": self.data,
            "PSV": self.data,
            "EOL": self.data,
        }

