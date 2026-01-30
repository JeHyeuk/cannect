from cannect.config import env
from cannect.core.can.rule import naming
from cannect.errors import CANDBError
from cannect.schema.candb import CanMessage, CanSignal

from datetime import datetime
from pandas import DataFrame, Series
from typing import Dict
import pandas as pd
import re


INFO = lambda revision: f"""* COMPANY: {env['COMPANY']}
* DIVISION: {env['DIVISION']}
* AUTHOR: {env['USERNAME']}
* CREATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* DB VERSION: {revision}
{env["COPYRIGHT"]} 

THIS MODEL IS AUTO-GENERATED.
"""

INLINE = f"""
/* ----------------------------------------------------------------------------------------------------
    Inline Function : Memory Copy
---------------------------------------------------------------------------------------------------- */
inline void __memcpy(void *dst, const void *src, size_t len) {{
    size_t i;
    char *d = dst;
    const char *s = src;
    for (i = 0; i < len; i++)
        d[i] = s[i];
}}

/* ----------------------------------------------------------------------------------------------------
    Inline Function : Message Counter Check
---------------------------------------------------------------------------------------------------- */
inline void cntvld(uint8 *vld, uint8 *timer, uint8 recv, uint8 calc, uint8 thres) {{
    if ( recv == calc ) {{
        *timer += 1;
        if ( *timer >= thres ) {{
            *timer = thres;
            *vld = 0;
        }}
    }}
    else {{
        *timer = 0;
        *vld = 1;
    }}
}}

/* ----------------------------------------------------------------------------------------------------
    Inline Function : CRC Check
---------------------------------------------------------------------------------------------------- */
inline void crcvld(uint8 *vld, uint8 *timer, uint8 recv, uint8 calc, uint8 thres) {{
    if ( recv == calc ) {{
        *timer = 0;
        *vld = 1;
    }}
    else {{
        *timer += 1;
        if ( *timer >= thres ) {{
            *timer = thres;
            *vld = 0;
        }}
    }}
}}

/* ----------------------------------------------------------------------------------------------------
    Inline Function : Alive Counter Check
---------------------------------------------------------------------------------------------------- */
inline void alvvld(uint8 *vld, uint8 *timer, uint8 recv, uint8 calc, uint8 thres) {{
    if ( ( recv == calc ) || ( (recv - calc) > 10 ) ) {{
        *timer += 1;
        if ( *timer >= thres ) {{
            *timer = thres;
            *vld = 0;
        }}
    }}
    else {{
        *timer = 0;
        *vld = 1;
    }}
}}
"""


def SignalDecode(signal:CanSignal, rule:naming=None) -> str:
    if signal.empty:
        return ""
    if not rule:
        rule = naming(signal.Message)
    name = signal.SignalRenamed if signal.SignalRenamed else signal.name
    size = 8 if signal.Length <= 8 else 16 if signal.Length <= 16 else 32
    buff = f'{rule.tag}.B.{name}'
    elem = f'{name}_Can'
    if signal.Message == "L_BMS_22_100ms" and signal.Length == 32:
        return f"""{elem} = (uint32)({buff}_1
                            + ({buff}_2 << 8)
                            + ({buff}_3 << 16)
                            + ({buff}_4 << 24));"""

    if signal["Value Type"].lower() == "unsigned":
        return f"{elem} = (uint{size}){buff};"

    if signal.SignedProcessing.lower() == "complement":
        if signal.Length in [8, 16, 32]:
            return f"{elem} = (sint{size}){buff};"
        else:
            msb = f"( {buff} >> {signal.Length - 1} ) && 1"
            neg = f"(sint{size})({buff} | {hex(2 ** size - 2 ** signal.Length).upper().replace('X', 'x')})"
            pos = f"(sint{size}){buff}"
            return f"{elem} = {msb} ? {neg} : {pos};"
    elif signal.SignedProcessing.lower() == "absolute":
        msb = f"( {buff} >> {signal.Length - 1} ) && 1"
        neg = f"(sint{size})( (~{buff} + 1) | {hex(2 ** size - 2 ** (signal.Length - 1)).upper().replace('X', 'x')} )"
        pos = f"(sint{size}){buff}"

        syn = f"{elem} = {msb} ? {neg} : {pos};"
        rtz = f"if ( {buff} == {hex(2 ** (signal.Length - 1)).upper().replace('X', 'x')} ) {{ {elem} = 0x0; }}"

        if str(signal.name) in ["TCU_TqRdctnVal", "TCU_EngTqLimVal", "L_TCU_TqRdctnVal", "L_TCU_EngTqLimVal"]:
            syn += f'\n{rtz}'
        return syn
    else:
        raise CANDBError("Signed Signal must be specified the processing method.")


class MessageValidator:
    def __init__(self, alv_or_crc:CanSignal, rule:naming=None):
        var = f'{alv_or_crc.name}_Can'
        calc =f'{alv_or_crc.name}Calc'
        self.decode = SignalDecode(alv_or_crc, rule)
        self.encode = ''
        if alv_or_crc.empty:
            self.calcCode = ''
            self.validate = ''
            return
        elif alv_or_crc.isCrc():
            self.calcCode = f'{calc} = CRC{alv_or_crc.Length}bit_Calculator.calc( {alv_or_crc.ID}, {rule.tag}.Data, {rule.dlc} );'
            self.validate = f'crcvld( &{rule.crcValid}, &{rule.crcTimer}, {var}, {calc}, {rule.thresholdTime} );'
        elif alv_or_crc.isAliveCounter():
            self.calcCode = f'{calc} = {var};'
            self.validate = f'alvvld( &{rule.aliveCountValid}, &{rule.aliveCountTimer}, {var}, {calc}, {rule.thresholdTime} );'
        else:
            pass
        return


class MessageCode:
    SEND_TYPE = {
        "P": "Periodic",
        "PE": "Periodic On Event",
        "EC": "Event On Change",
        "EW": "Event On Write",
    }

    def __init__(self, message:CanMessage, exclude_tsw:bool=True):
        self.message = message
        self.name = name = str(message.name)
        self.names = naming(self.name)
        self.exclude_tsw = exclude_tsw

        self.srv_name = lambda md: f"#define COMPILE_UNUSED__{md.upper()}_IMPL__{name}"
        return

    def __getitem__(self, item):
        return self.message[item]

    def messageAlign(self) -> list:
        buffer = [f"Reserved_{n // 8}" for n in range(8 * self["DLC"])]
        self.message.ITERATION_INCLUDES_CRC = self.message.ITERATION_INCLUDES_ALIVECOUNTER = True
        for sig in self.message:
            index = sig.StartBit
            while index < (sig.StartBit + sig.Length):
                buffer[index] = sig.SignalRenamed if sig.SignalRenamed else sig.Signal
                index += 1

        # Exception
        cnt = {}
        for n, sig in enumerate(buffer.copy()):
            if sig.startswith('xEV_Tot'):
                if not sig in cnt:
                    cnt[sig] = 0
                buffer[n] = f'{buffer[n]}_{(cnt[sig] // 8) + 1}'
                cnt[sig] += 1

        aligned = []
        count, name = 0, buffer[0]
        for n, sig in enumerate(buffer):
            if sig == name:
                count += 1
                if n == 8 * self["DLC"] - 1:
                    aligned.append(f"uint32 {name} : {count};")
            else:
                aligned.append(f"uint32 {name} : {count};")
                count, name = 1, sig

        eigen = []
        aligned_copy = aligned.copy()
        for n, struct in enumerate(aligned):
            label = struct.split(" : ")[0].replace("uint32 ", "")
            if label in eigen:
                aligned_copy[n] = aligned_copy[n].replace(label, f'{label}_{eigen.count(label)}')
            eigen.append(label)

        return aligned_copy

    def signalDecode(self, spliter:str="\n\t") -> str:
        code = []
        for sig in self.message:
            if sig.isAliveCounter() or sig.isCrc():
                continue
            code.append(SignalDecode(sig, self.names))
        return spliter.join(code)

    @property
    def def_name(self) -> str:
        chn = "PL2" if self["Channel"] == "H" else "PL1" if self["Channel"] == "L" else "P"
        bsw = f"CAN_MSGNAME_{self['Message']}_{chn}"
        if self["Message"] == "EGSNXUpStream_Data":
            bsw = "CAN_MSGNAME_EGSNXUpStream_B1_data_1"
        if self["Message"] == "EGSNXUpStream_Req":
            bsw = "CAN_MSGNAME_EGSNXUpStream_B1_Rqst"
        if self["Message"] == "HCU_11_P_00ms":
            bsw = "CAN_MSGNAME_HCU_11_00ms_P"
        if self["Message"] == "HCU_11_H_00ms":
            bsw = "CAN_MSGNAME_HCU_11_00ms_PL2"
        if self["Message"] == "IMU_01_10ms":
            bsw = "CAN_MSGNAME_YRS_01_10ms_P"
        if self.message.isTsw() and self.exclude_tsw:
            bsw = 255
        asw = f'MSGNAME_{naming(self["Message"]).tag}'
        return f"#define {asw}\t{bsw}"

    @property
    def struct(self) -> str:
        aligned = '\n\t\t'.join(self.messageAlign())
        return f"""
/* ------------------------------------------------------------------------------
 MESSAGE\t\t\t: {self["Message"]}
 MESSAGE ID\t\t: {self["ID"]}
 MESSAGE DLC\t: {self["DLC"]}
 SEND TYPE\t\t: {self["Send Type"]}
-------------------------------------------------------------------------------- */
typedef union {{
    uint8 Data[{self["DLC"]}];
    struct {{
        {aligned}
    }} B;
}} CanFrm_{self.names.tag};"""

    @property
    def method(self) -> str:
        names = self.names
        aliveCounter = MessageValidator(self.message.aliveCounter, names)
        crc = MessageValidator(self.message.crc, names)
        code = f"""
/* ------------------------------------------------------------------------------
 MESSAGE\t\t\t: {self.name}
 MESSAGE ID\t\t: {self["ID"]}
 MESSAGE DLC\t: {self["DLC"]}
 SEND TYPE\t\t: {self.SEND_TYPE[self["Send Type"]]}
 VERSION\t\t\t: {self["Version"]}
-------------------------------------------------------------------------------- */
if ( CanFrm_Recv( MSGNAME_{names.tag}, {names.buffer}, &{names.dlc} ) == CAN_RX_UPDATED ) {{

    CanFrm_{names.tag} {names.tag} = {{0, }};
    __memcpy( {names.tag}.Data, {names.buffer}, {names.dlc} );

    { crc.decode }
    { crc.calcCode }
    { aliveCounter.decode }

    { self.signalDecode() }

    { names.counter }++;
}}

cntvld( &{names.messageCountValid}, &{names.messageCountTimer}, {names.counter}, {names.counterCalc}, {names.thresholdTime} );
{ crc.validate }
{ aliveCounter.validate }

{ names.counterCalc } = { names.counter };
{ aliveCounter.calcCode }
"""
        pcode = code[1:].splitlines()
        ccode = []
        for n, line in enumerate(pcode):
            if n:
                prev_line = pcode[n-1].replace("\t", "").replace(" ", "")
                curr_line = line.replace("\t", "").replace(" ", "")
                if prev_line == curr_line == "":
                    continue
            ccode.append(line)
        return "\n".join(ccode)

    def to_rx(self, model: str) -> str:
        tab, i = '\t', 0
        send_type = {
            "P": "Periodic",
            "PE": "Periodic On Event",
            "EC": "Event On Change",
            "EW": "Event On Write",
        }
        syntax = f"""
/* ------------------------------------------------
 MESSAGE\t\t\t: {self["Message"]}
 MESSAGE ID\t\t: {self["ID"]}
 MESSAGE DLC\t: {self["DLC"]}
 SEND TYPE\t\t: {send_type[self["Send Type"]]}
 CHANNEL\t\t\t: {self["Channel"]}-CAN
-------------------------------------------------- */"""
        if self["SystemConstant"]:
            syntax += f"\n#if ( {self['SystemConstant']} )"
        if self["Codeword"]:
            syntax += f"\nif ( {self['Codeword']} ) {{"
            i += 1
        syntax += f"\n{tab * i}{model.upper()}_IMPL__{self['Message']}();\n"
        if self["Codeword"]:
            syntax += f"}}\n"
        if self["SystemConstant"]:
            syntax += f"#endif\n"
        return syntax

    @classmethod
    def method_contains_message(cls, context: Dict[str, str]) -> DataFrame:
        status = {}
        for method, code in context.items():
            if code is None:
                status[method] = None
            else:
                fs = [f.split("__")[-1] for f in re.findall(r'\bCOMDEF_\w*', code)]
                status[method] = Series(index=fs, data=fs)
        return pd.concat(status, axis=1)

if __name__ == "__main__":
    from pyems.candb import CAN_DB

    testDB = CAN_DB.to_developer_mode("HEV")

    code = MessageCode(testDB.messages["L_BMS_22_100ms"])
    print(code.def_name)
    print(code.method)