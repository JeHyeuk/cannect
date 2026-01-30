from cannect.core.can.rule import naming
from cannect.core.testcase.unitcase import UnitTestCase
from pandas import Series


class SignalDecodingUnit(UnitTestCase):

    def __init__(self, sig:Series, **override):
        nm = naming(sig)
        sg = sig.SignalRenamed if sig.SignalRenamed else sig.name
        var = f"{sg}_Can"
        if sg in ["Power_Limit_Dchg", "Power_Limit_Chg"]:
            var = f"{sg}_Bms"
        if sig["ECU"] == "MHSG" and not sig["Message"] == "SCU_DIAG2":
            var = f"{sg}_Mhsg"
        unit = '-' if not sig.Unit else sig.Unit
        index = self._index(sig)
        buff = "\n".join([f"{nm.buffer}_[{n}]" for n in index])
        vals = '\n'.join(['Unconcerned'] * len(index))
        expr = f"{index[0]}:{index[-1]}" if len(index) > 1 else f"{index[0]}"
        kwargs = {
            "Category": "UNIT",
            "Group": "CAN",
            "Test Case Name": "Signal Decoding Test",
            "Test Purpose, Description": f"{sg} @{nm}({sig.ID}) Decoding Test",
            "Test Execution (TE) - Description": f"CAN Signal: Transmit {sg} @{nm}\n"
                                                 f"- ON Vehicle: Followed by the specification\n"
                                                 f"- ON T-Bench: Comprehensive range transmission",
            "TE-Variable": f"{nm.counter}\n"
                           f"{buff}",
            "TE-Compare": "'=",
            "TE-Value": f"△1\n"
                        f"{vals}",
            "Expected Results (ER) - Description": f"ON Receiving\n"
                                                   f"- Message Counter = △1\n"
                                                   f"- Signal Variable = Buffer[{expr}]\n"
                                                   f"Compatible Signal Quality with DB",
            "ER-Variable": f"{var}",
            "ER-Compare": "'=",
            "ER-Value": f"{nm.buffer}_[{expr}]",
            "Test Result Description": f"ON Receiving\n"
                                       f"- {nm.counter} = △1\n"
                                       f"- {var} = {nm.buffer}_[{expr}]\n"
                                       f"  * Length(Bit): {sig.Length}\n"
                                       f"  * Start Bit:  {sig.StartBit}\n\n"
                                       f"Compatible Signal Quality with DB\n"
                                       f"- Factor: {sig.Factor}\n"
                                       f"- Offset: {sig.Offset}\n"
                                       f"- Min: {sig.Offset} [{unit}]\n"
                                       f"- Max: {sig.Factor * (2 ** sig.Length - 1) + sig.Offset} [{unit}]",
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
