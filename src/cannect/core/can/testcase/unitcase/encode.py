from cannect.core.can.rule import naming
from cannect.core.testcase.unitcase import UnitTestCase
from pandas import Series


class SignalEncodingUnit(UnitTestCase):

    def __init__(self, sig:Series, **override):
        nm = naming(sig)
        sg = sig.SignalRenamed if sig.SignalRenamed else sig.name
        var = f"{sg}_Ems"
        if sg in ["CLU_LoFuelWrngSta", "DATC_OutTempSnsrVal", "VVDIN_EMS_ANTI_STKBACK_POS"]:
            var = f"{sg}_Can"
        if sig["Message"] in ["EMS_CVVD1", "EMS_LDCBMS1"]:
            var = f"{sg}_Can"
        if sig["Message"] in ["MASTER_CTRL_REQ", "MASTER_EXT_REQ"]:
            var = f"{sg}_Mhsg"

        index = self._index(sig)
        buff = "\n".join([f"{nm.buffer}_[{n}]" for n in index])
        expr = f"{index[0]}:{index[-1]}" if len(index) > 1 else f"{index[0]}"
        kwargs = {
            "Category": "UNIT",
            "Group": "CAN",
            "Test Case Name": "Signal Encoding Test",
            "Test Purpose, Description": f"{sg} @{nm}({sig.ID}) Decoding Test",
            "Test Execution (TE) - Description": f"CAN Signal: Automatically transmitted {sg} @{nm}\n"
                                                 f"- ON Vehicle: Nothing to do\n"
                                                 f"- ON T-Bench: Nothing to do",
            "TE-Variable": f"{var}",
            "TE-Compare": "'=",
            "TE-Value": f"ASW-Dependent",
            "Expected Results (ER) - Description": f"ON Transmitting\n"
                                                   f"- Buffer[{expr}] = Signal Variable\n"
                                                   f"Compatible Signal Quality with DB",
            "ER-Variable": f"{buff}",
            "ER-Compare": "'=",
            "ER-Value": f"{var}",
            "Test Result Description": f"ON Transmitting\n"
                                       f"- {nm.buffer}_[{expr}] = {var}\n"
                                       f"  * Length(Bit): {sig.Length}\n"
                                       f"  * Start Bit:  {sig.StartBit}\n\n"
                                       f"Compatible Signal Quality with DB\n"
                                       f"- Factor: {sig.Factor}\n"
                                       f"- Offset: {sig.Offset}\n"
                                       f"- Min: {sig.Offset} [{sig.Unit}]\n"
                                       f"- Max: {sig.Factor * (2 ** sig.Length - 1) + sig.Offset} [{sig.Unit}]",
        }
        kwargs.update(override)
        super().__init__(**kwargs)
        return

    @staticmethod
    def _index(sig:Series) -> range:
        start_byte = sig.StartBit // 8
        end_bit = sig.StartBit + sig.Length
        end_byte = end_bit // 8
        if (end_bit / 8) > end_byte:
            end_byte += 1
        return range(start_byte, end_byte, 1)
