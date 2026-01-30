from cannect.core.can.rule import naming
from cannect.core.testcase.unitcase import UnitTestCase
from pandas import DataFrame, Series


class Asw2CanUnit(UnitTestCase):

    def __init__(self, sig:Series, io:DataFrame, **override):
        nm = naming(sig)
        unit = '-' if not sig.Unit else sig.Unit
        model = io["module"].values[0]
        path = io["Path"].values[0]

        inputs = io[io["dir"] == 'input'].copy()
        inputs.loc[inputs["value"].isna(), "value"] = "External"
        outputs = io[io["dir"] == 'output'].copy()
        var = ",".join([v for v in outputs["name"] if v.startswith(outputs["Signal"].values[0])])
        o, c = '{', '}'
        kwargs = {
            "Category": "UNIT",
            "Group": "CAN",
            "Test Case Name": "Signal Interface Test",
            "Test Purpose, Description": f"{sig.name} @{nm}({sig.ID}) Interface Test",
            "Test Execution (TE) - Description": f"ENGINE ON/RUN\n"
                                                 f"- 차량 검증 시: 차량 주행에 따름\n"
                                                 f"- 정적 검증 시: 오프라인 SW 검증",
            "TE-Variable": "\n".join(inputs["name"]),
            "TE-Compare": "'" + "\n".join(["="] * len(inputs)),
            "TE-Value": "\n".join(inputs["value"]),
            "Expected Results (ER) - Description": f"정상 인터페이스\n"
                                                   f"- 로직 모델: %{model}{path}\n"
                                                   f"- CAN 신호 변수 = {var}\n"
                                                   f"신호 속성 DB 정합",
            "ER-Variable": "\n".join(outputs["name"]),
            "ER-Compare": "'" + "\n".join(["="] * len(outputs)),
            "ER-Value": "\n".join(["Calculated"] * len(outputs)),
            "Test Result Description": f"정상 인터페이스\n"
                                       f"- {var} = {o}%{model}{path}{c}\n\n"
                                       f"신호 속성\n"
                                       f"- Factor: {sig.Factor}\n"
                                       f"- Offset: {sig.Offset}\n"
                                       f"- Min: {sig.Offset} [{unit}]\n"
                                       f"- Max: {sig.Factor * (2 ** sig.Length - 1) + sig.Offset} [{unit}]\n"
                                       f"* 차량 주행 시 Min/Max 검증 확인 불가" ,
        }
        kwargs.update(override)
        super().__init__(**kwargs)
        return
