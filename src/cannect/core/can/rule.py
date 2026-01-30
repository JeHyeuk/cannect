from pandas import Series
from typing import Dict, Union, Hashable
import re


MESSAGE_RENAME = {
    # NEW NAME: OLD NAME #
    "SCU_DIAG": 'MHSG_STATE3',
    "SCU_DIAG2": "MHSG_STATE4",
    "SCU_FUNCTIONAL": "MHSG_STATE2",
    "SCU_STATUS": "MHSG_STATE1",
    "MASTER_CTRL_REQ": "EMS_MHSG1",
    "MASTER_EXT_REQ": "EMS_MHSG2",
    "MASTER_SPEED_REQ": "EMS_MHSG_SPEED",
    "MASTER_STARTER_REQ": "EMS_MHSG_STARTER"
}
class naming(object):

    def __init__(self, message: Union[str, Dict, Series, Hashable], hw:str='ICE'):

        if isinstance(message, Series) or isinstance(message, Dict):
            self.message = message["Message"]
        elif isinstance(message, str):
            self.message = message
        elif isinstance(message, Hashable):
            self.message = str(message)
        else:
            raise TypeError(f"Unknown type for message; {message}")
        self.name = self.message

        """
        [예외 처리]
        DB 상 이름이 매우 길거나 구 DB상 이름으로 개발되었으나 신 DB에서 이름이 바뀐 경우
        """
        if self.message.startswith("EGSNXUpStream"):
            self.message = self.message.replace("UpStream", "")
        if self.message == "Main_Status_Rear":
            self.message = "NOx1Down"
        if self.message == "O2_Rear":
            self.message = "NOx1Ext"
        if self.message.startswith("LEMS"):
            self.message = f"L_{self.message[1:]}"
        if self.message in MESSAGE_RENAME:
            self.message = MESSAGE_RENAME[self.message]


        """
        [Message Name to Element Name : Base]
        ASCET CAN 모델에 사용하는 Element Naming Rule 정의

        1. ASCET Element(Variable)에 사용하는 Message Name
        Rule) split('_') --> capitalize() --> join()
              * Under-Bar 없는 경우 capitalize()만 수행
              * CAN-FD의 경우 메시지 주기 정보 제거
              * Local CAN 식별자 L은 항상 대문자
              * HEV 식별자 H는 항상 대문자
        e.g.)    Original Name   |   Rule Base Name
              ----------------------------------------
                ABS_ESC_01_10ms  |         AbsEsc01
                    HU_GW_PE_01  |         HuGwPe01
                         FPCM11  |           Fpcm11
                   EMS_14_200ms  |            Ems14
                   HTCU_04_10ms  |           HTcu04
                 L_HTCU_10_10ms  |          LHTcu10
        """
        splits = self.message.split('_')
        splits = [split.lower().capitalize() for split in splits if not 'ms' in split]
        self.base = base = ''.join(splits)
        self.number = ''.join(re.findall(r'\d+', base))
        if self.message.startswith("NOx"):
            self.base = base = self.message
        if "Htcu" in base:
            self.base = base = base.replace("Htcu", "HTcu")
        if self.message.startswith("L_EMS"):
            self.base = base = f"L_EMS{splits[-1]}"
        if self.message == "EMS_LDCBMS1":
            self.base = base = "EmsLdcBms1"
        if self.message.startswith("MHSG"):
            self.base = base = f"StMhsg{splits[-1][-1]}"
        self.pascal = base

        self.root = root = ''.join([char for char in base if char.isalpha()])
        if "Fd" in root:
            self.root = root = root.replace("Fd", "")
        if root == "BdcSmk":
            self.root = root = "Bdc"
        if self.message == "WHL_01_10ms":
            self.root = root = "Abs"
        for key in ["Bdc", "Hu", "Ilcu", "Pdc", "Sbcm", "Swrc"]:
            if root.startswith(key):
                self.root = root = key
                break

        """
        2. ASECT Hierarchy에 사용하는 Message Name
        Rule) split('_') --> upper() --> join()
              * Under-Bar 없는 경우 capitalize()만 수행
              * CAN-FD의 경우 메시지 주기 정보 제거
        e.g.)    Original Name   |   Rule Base Name
              ----------------------------------------
                ABS_ESC_01_10ms  |         ABSESC01
                    HU_GW_PE_01  |         HUGWPE01
                         FPCM11  |           FPCM11
                   EMS_14_200ms  |            EMS14
                   HTCU_04_10ms  |           HTCU04
                 L_HTCU_10_10ms  |          LHTCU10
        """
        splits = [split.upper() for split in splits]
        self.hierarchy = self.tag = self.upper = tag = ''.join(splits)
        if self.message.startswith("MHSG"):
            self.hierarchy = self.tag = self.upper = tag = f"MHSG{splits[-1][-1]}"

        """
        [Element Names]
        1. Buffer        : Can_{base}Buf_A
        2. DLC           : Can_{base}Size
        3. Counter       : Can_ct{base}
        4. Counter Calc. : Can_ct{base}Calc
        4. Timeout       : Can_tiFlt{base}_C
        5. Timer         : Can_tiFlt{base}{Msg or Alv or Crc}
        6. Validity      : FD_cVld{base}{Msg or Alv or Crc}
        7. Message Valid : FD_cVld{base}
        8. Status        : Com_st{base}

        """
        self.method = f'_{self.message}'
        self.buffer = f"Can_{base}Buf_A"
        self.dlc = f"Can_{base}Size"
        self.counter = f"Can_ct{base}"
        self.counterCalc = f"Can_ct{base}Calc"
        self.thresholdTime = f"Can_tiFlt{base}_C"

        self.messageCountTimer = f"Can_tiFlt{base}Msg"
        self.messageCountValid = f"FD_cVld{base}Msg"
        self.aliveCountTimer = f"Can_tiFlt{base}Alv"
        self.aliveCountValid = f"FD_cVld{base}Alv"
        self.crcTimer = f"Can_tiFlt{base}Crc"
        self.crcValid = f"FD_cVld{base}Crc"
        self.messageValid = f"FD_cVld{base}"
        self.status = f"Com_st{base}"

        # 진단 모듈 사용 Naming
        self.detectionThresholdTime = f"CanD_tiMonDet{root}_C"
        self.detectionThreshold = f"CanD_ctDet{root}_C"
        self.eepReset = f"CanD_RstEep{root}_C"

        self.diagnosisChannel = f"CanD_cEnaDiagBus1"
        self.detectionChannel = f"CanD_cEnaDetBus1{root}"
        self.eepIndex = f"EEP_FD{tag}"
        self.eep = f"EEP_stFD{tag}"
        self.eepReader = f"CanD_stRdEep{base}"
        self.fid = f"Fid_FD{tag}D"
        self.debounceTime = f"CanD_tiFlt{base}_C"
        self.debounceTimerMsg = f"CanD_tiFlt{base}Msg"
        self.debounceTimerCrc = f"CanD_tiFlt{base}Crc"
        self.debounceTimerAlv = f"CanD_tiFlt{base}Alv"
        self.deveMsg = f"DEve_FD{base}Msg"
        self.deveCrc = f"DEve_FD{base}Crc"
        self.deveAlv = f"DEve_FD{base}Alv"
        self.diagnosisMsg = f"CanD_cErr{base}Msg"
        self.diagnosisCrc = f"CanD_cErr{base}Crc"
        self.diagnosisAlv = f"CanD_cErr{base}Alv"
        self.detectionCounter = f"CanD_ctDet{base}"
        self.detectionEnable = f"CanD_cEnaDet{base}"
        self.diagnosisEnable = f"CanD_cEnaDiag{base}"

        """
        3. Exceptions
          1) DB 개정에 따라 메시지 이름이 변경되었으나 Binding 우려로 인해 기존 Naming을 유지해야 하는 경우
          2) 개발자 실수에 따라 양산 반영된 오기 Naming이 Binding 우려로 인해 기존 Naming을 유지해야 하는 경우
          3) DB 메시지 이름의 오타, 오탈 또는 길이 등의 사유로 인해 임의로 Naming을 변경한 경우
          4) 상기 사유 외 예외 처리가 인정되는 경우 
        """
        if hw == "HEV":
            self.eep = f"EEP_stHevFD{base}"
            if self.message == "ABS_ESC_01_10ms":
                self.eep = "EEP_stHevFDAbs01"
            if self.message == "FPCM_01_100ms" :
                self.eep = "EEP_stHevHSFpcm01"
            if self.message == "SBCM_DRV_03_200ms":
                self.eep = "EEP_stFDSBCMDRV03"
            if self.message == "SBCM_DRV_FD_01_200ms":
                self.eep = "EEP_stFDSBCMDRVFD01"
        if self.message.startswith("EMS_CVVD"):
            self.buffer = f"Can_{base}_Buf_A"
        if (self.message.startswith('BMS') or self.message.startswith('LDC')) and len(self.message) == 4:
            self.messageCountValid = f"Can_cVldMsgCt{base}"
            self.aliveCountValid = f"Can_cVldAlvCt{base}"
            self.crcValid = f"Can_cVldChks{base}"
            self.eep = f"EEP_st48V{base}"
            self.eepIndex = f"EEP_48V_DCAN{tag}"
        if self.message.startswith('MHSG'):
            self.messageCountValid = f"Can_cVldMsgCt{base}"
            self.aliveCountValid = f"Can_cVldAlvCt{base}"
            self.crcValid = f"Can_cVldChks{base}"
            self.eep = f"EEP_st48V{base.replace('St', '')}"
            self.eepIndex = f"EEP_48V_DCAN{tag}"
            self.detectionEnable = f"CanD_cEnaDet{base.replace('St', '')}"
            self.deveMsg = f"DEve_Can{base.replace('St', '')}Msg"
            self.deveCrc = f"DEve_Can{base.replace('St', '')}Chks"
            self.deveAlv = f"DEve_Can{base.replace('St', '')}Alv"
        if self.message.startswith('CVVD'):
            self.messageCountValid = f"Can_cVldMsgCnt{base}"
            self.aliveCountValid = f"Can_cVldAlvCnt{base}"
            self.crcValid = f"Can_cVldCRC{base}"
            self.eep = f"EEP_st{tag}"
            self.eepIndex = f"EEP_DCAN{tag}"
        if self.message == "NOx1Down":
            self.fid = "Fid_CanNOx1DownD"
            self.deveMsg = "DEve_CanNOx1DownMsg"
            self.eepIndex = f"EEP_DCAN{tag}"
        if self.message == "NOx1Ext":
            self.fid = "Fid_CanNOx1ExtD"
            self.deveMsg = "DEve_CanNOx1ExtMsg"
            self.eepIndex = f"EEP_DCAN{tag}"
        if self.message == "ABS_ESC_01_10ms":
            self.deveMsg = "DEve_FDAbs01Msg"
            self.deveCrc = "DEve_FDAbs01Crc"
            self.deveAlv = "DEve_FDAbs01Alv"
        return

    def __str__(self) -> str:
        return self.message


if __name__ == "__main__":

    rule = naming("FPCM_01_100ms")
    print(rule.root)