from cannect.core.can.rule import naming
from cannect.core.testcase.unitcase import UnitTestCase
from cannect.schema.datadictionary import DataDictionary


def detection(message:str, **override) -> UnitTestCase:
    """
    UNIT TEST CASE FOR CAN MESSAGE AUTO-DETECTION
    """
    nm = naming(message)
    dd = DataDictionary()
    dd.detection_time           = nm.detectionThresholdTime
    dd.detection_limit          = nm.detectionThreshold
    dd.message_counter_valid    = nm.messageCountValid
    dd.detection_counter        = nm.detectionCounter
    dd.detection_eep            = nm.eep
    dd.detection_enable         = nm.detectionEnable
    dd.diagnosis_enable         = nm.diagnosisEnable


    # VARIABLE NAMING
    # TE-VARIABLE
    te = "\n".join([v for v in [
        dd.detection_time,
        dd.detection_limit,
        dd.message_counter_valid
    ] if v])
    tv = "\n".join(['△1' if v == dd.message_counter_valid else '-' for v in te.split("\n")])

    # ER-VARIABLE
    er = "\n".join([v for v in [
        dd.detection_counter,
        dd.detection_eep,
        dd.detection_enable,
        dd.diagnosis_enable
    ] if v])
    ev = "\n".join(['△1', '0 → 1', '0 → 1 → 0', '0 → 1'])

    kwargs = {
        "Category": "UNIT",
        "Group": "CAN",
        "Test Case Name": "Message Detection",
        "Test Purpose, Description": f"Message: {nm}\n"
                                     f"1) Message Auto-Detect and Store To EEPROM\n"
                                     f"2) Message Diagnosis Enabled",
        "Test Execution (TE) - Description": f"1) Message: '{nm}' Exist On CAN BUS\n"
                                             f"2) Trigger IG ON To Enter Detection\n",
        "TE-Variable": f"{te}",
        "TE-Compare": "'=",
        "TE-Value": f"{tv}",
        "Expected Results (ER) - Description": f"1) Message Auto-Detect and Store To EEPROM\n"
                                               f"2) Message Diagnosis Enabled",
        "ER-Variable": f"{er}",
        "ER-Compare": "'=",
        "ER-Value": f"{ev}",
        "Test Result Description": f"Message: {nm}\n"
                                   f"1) Message Auto-Detect and Store To EEPROM\n"
                                   f" - {dd.detection_enable} = 1\n"
                                   f" - {dd.diagnosis_enable} = 0\n"
                                   f" - {dd.detection_counter} = △1\n"
                                   f" * {dd.detection_eep} = 0\n\n"
                                   f"2) Message Diagnosis Enabled\n"
                                   f" - {dd.detection_enable} = 0\n"
                                   f" - {dd.diagnosis_enable} = 1\n"
                                   f" - {dd.detection_counter} = {dd.detection_limit}\n"
                                   f" * {dd.detection_eep} = 0 → 1"
    }
    kwargs.update(override)
    return UnitTestCase(**kwargs)


def diagnosis_counter(message:str, **override) -> UnitTestCase:
    """
    UNIT TEST CASE FOR CAN MESSAGE COUNTER DIAGNOSIS
    """
    nm = naming(message)
    dd = DataDictionary()
    dd.message_valid        = nm.messageCountValid
    dd.diagnosis_enable     = nm.diagnosisEnable
    dd.debounce_threshold   = nm.debounceTime
    dd.debounce_timer       = nm.debounceTimerMsg
    dd.diagnosis_bit        = nm.diagnosisMsg
    dd.deve                 = nm.deveMsg

    # VARIABLE NAMING
    # TE-VARIABLE
    te = "\n".join([v for v in [
        dd.message_valid,
        dd.diagnosis_enable,
        dd.debounce_threshold
    ] if v])
    tv = "\n".join(['Simulated', '1', '2.0'])

    # ER-VARIABLE
    er = "\n".join([v for v in [
        dd.debounce_timer,
        dd.diagnosis_bit,
        dd.deve,
    ] if v])
    ev = "\n".join(['△0.1', '0:No Diag / 1:Diag', 'DSM'])

    kwargs = {
        "Category": "UNIT",
        "Group": "CAN",
        "Test Case Name": "Message Diagnosis",
        "Test Purpose, Description": f"Message: {nm}\n"
                                     f"1) Diagnosis Debounce on Message Counter Fault\n"
                                     f"2) Diagnosis Report",
        "Test Execution (TE) - Description": f"1) Message: '{nm}' Exist On CAN BUS\n"
                                             f"2) Simulate Message Fail Case",
        "TE-Variable": f"{te}",
        "TE-Compare": "'=",
        "TE-Value": f"{tv}",
        "Expected Results (ER) - Description": f"1) Diagnosis Debounce on Message Counter Fault\n"
                                               f"2) Diagnosis Report",
        "ER-Variable": f"{er}",
        "ER-Compare": "'=",
        "ER-Value": f"{ev}",
        "Test Result Description": f"Message: {nm}\n"
                                   f"{dd.diagnosis_enable} = 1"                                   
                                   f"1) Diagnosis Debounce on Message Counter Fault\n"
                                   f"1.1) Debounce Case"
                                   f" - {dd.message_valid} = 0\n"
                                   f" - {dd.debounce_timer} = +△0.1\n"
                                   f"   * ~{dd.debounce_threshold}\n\n"
                                   f"1.2) Healing Case"
                                   f" - {dd.message_valid} = 0 → 1\n"
                                   f" - {dd.debounce_timer} = -△0.1\n"
                                   f"   * ~0\n\n"
                                   f"2) Diagnosis Report\n"
                                   f" - {dd.debounce_timer} = {dd.debounce_threshold}\n"
                                   f" - {dd.diagnosis_bit} = 1\n"
                                   f" * {dd.deve} = 1.6E+04"
    }
    kwargs.update(override)
    return UnitTestCase(**kwargs)

def diagnosis_alive(message:str, **override) -> UnitTestCase:
    """
    UNIT TEST CASE FOR CAN ALIVE COUNTER DIAGNOSIS
    """
    nm = naming(message)
    dd = DataDictionary()
    dd.alive_valid          = nm.aliveCountValid
    dd.diagnosis_enable     = nm.diagnosisEnable
    dd.debounce_threshold   = nm.debounceTime
    dd.debounce_timer       = nm.debounceTimerAlv
    dd.diagnosis_bit        = nm.diagnosisAlv
    dd.deve                 = nm.deveAlv

    # VARIABLE NAMING
    # TE-VARIABLE
    te = "\n".join([v for v in [
        dd.alive_valid,
        dd.diagnosis_enable,
        dd.debounce_threshold
    ] if v])
    tv = "\n".join(['Simulated', '1', '2.0'])

    # ER-VARIABLE
    er = "\n".join([v for v in [
        dd.debounce_timer,
        dd.diagnosis_bit,
        dd.deve,
    ] if v])
    ev = "\n".join(['△0.1', '0:No Diag / 1:Diag', 'DSM'])

    kwargs = {
        "Category": "UNIT",
        "Group": "CAN",
        "Test Case Name": "Alive Counter Diagnosis",
        "Test Purpose, Description": f"Message: {nm}\n"
                                     f"1) Diagnosis Debounce on Alive Counter Fault\n"
                                     f"2) Diagnosis Report",
        "Test Execution (TE) - Description": f"1) Message: '{nm}' Exist On CAN BUS\n"
                                             f"2) Simulate Alive Fail Case\n",
        "TE-Variable": f"{te}",
        "TE-Compare": "'=",
        "TE-Value": f"{tv}",
        "Expected Results (ER) - Description": f"1) Diagnosis Debounce on Alive Counter Fault\n"
                                               f"2) Diagnosis Report",
        "ER-Variable": f"{er}",
        "ER-Compare": "'=",
        "ER-Value": f"{ev}",
        "Test Result Description": f"Message: {nm}\n"
                                   f"{dd.diagnosis_enable} = 1"                                   
                                   f"1) Diagnosis Debounce on Alive Counter Fault\n"
                                   f"1.1) Debounce Case"
                                   f" - {dd.alive_valid} = 0\n"
                                   f" - {dd.debounce_timer} = +△0.1\n"
                                   f"   * ~{dd.debounce_threshold}\n\n"
                                   f"1.2) Healing Case"
                                   f" - {dd.alive_valid} = 0 → 1\n"
                                   f" - {dd.debounce_timer} = -△0.1\n"
                                   f"   * ~0\n\n"
                                   f"2) Diagnosis Report\n"
                                   f" - {dd.debounce_timer} = {dd.debounce_threshold}\n"
                                   f" - {dd.diagnosis_bit} = 1\n"
                                   f" * {dd.deve} = 1.6E+04"
    }
    kwargs.update(override)
    return UnitTestCase(**kwargs)


def diagnosis_crc(message:str, **override) -> UnitTestCase:
    """
    UNIT TEST CASE FOR CAN CRC DIAGNOSIS
    """
    nm = naming(message)
    dd = DataDictionary()
    dd.crc_valid            = nm.crcValid
    dd.diagnosis_enable     = nm.diagnosisEnable
    dd.debounce_threshold   = nm.debounceTime
    dd.debounce_timer       = nm.debounceTimerCrc
    dd.diagnosis_bit        = nm.diagnosisCrc
    dd.deve                 = nm.deveCrc

    # VARIABLE NAMING
    # TE-VARIABLE
    te = "\n".join([v for v in [
        dd.crc_valid,
        dd.diagnosis_enable,
        dd.debounce_threshold
    ] if v])
    tv = "\n".join(['Simulated', '1', '2.0'])

    # ER-VARIABLE
    er = "\n".join([v for v in [
        dd.debounce_timer,
        dd.diagnosis_bit,
        dd.deve,
    ] if v])
    ev = "\n".join(['△0.1', '0:No Diag / 1:Diag', 'DSM'])

    kwargs = {
        "Category": "UNIT",
        "Group": "CAN",
        "Test Case Name": "CRC Diagnosis",
        "Test Purpose, Description": f"Message: {nm}\n"
                                     f"1) Diagnosis Debounce on CRC Fault\n"
                                     f"2) Diagnosis Report",
        "Test Execution (TE) - Description": f"1) Message: '{nm}' Exist On CAN BUS\n"
                                             f"2) Simulate CRC Fail Case\n",
        "TE-Variable": f"{te}",
        "TE-Compare": "'=",
        "TE-Value": f"{tv}",
        "Expected Results (ER) - Description": f"1) Diagnosis Debounce on CRC Fault\n"
                                               f"2) Diagnosis Report",
        "ER-Variable": f"{er}",
        "ER-Compare": "'=",
        "ER-Value": f"{ev}",
        "Test Result Description": f"Message: {nm}\n"
                                   f"{dd.diagnosis_enable} = 1"                                   
                                   f"1) Diagnosis Debounce on CRC Fault\n"
                                   f"1.1) Debounce Case"
                                   f" - {dd.crc_valid} = 0\n"
                                   f" - {dd.debounce_timer} = +△0.1\n"
                                   f"   * ~{dd.debounce_threshold}\n\n"
                                   f"1.2) Healing Case"
                                   f" - {dd.crc_valid} = 0 → 1\n"
                                   f" - {dd.debounce_timer} = -△0.1\n"
                                   f"   * ~0\n\n"
                                   f"2) Diagnosis Report\n"
                                   f" - {dd.debounce_timer} = {dd.debounce_threshold}\n"
                                   f" - {dd.diagnosis_bit} = 1\n"
                                   f" * {dd.deve} = 1.6E+04"
    }
    kwargs.update(override)
    return UnitTestCase(**kwargs)

def fid_inhibit(message:str, **override) -> UnitTestCase:
    """
    UNIT TEST CASE FOR CAN FID INHIBIT
    """
    nm = naming(message)
    dd = DataDictionary()
    dd.fid                  = nm.fid
    dd.debounce_threshold   = nm.debounceTime
    dd.debounce_timer_msg   = nm.debounceTimerMsg
    dd.debounce_timer_alv   = nm.debounceTimerAlv
    dd.debounce_timer_crc   = nm.debounceTimerCrc

    # VARIABLE NAMING
    # TE-VARIABLE
    te = "\n".join([v for v in [
        "IgKey_On",
        dd.fid,
        dd.debounce_threshold,
    ] if v])
    tv = "\n".join(['1', '(NOT) 128 (Inhibit)', '2.0'])

    # ER-VARIABLE
    er = "\n".join([v for v in [
        dd.debounce_timer_msg,
        dd.debounce_timer_alv,
        dd.debounce_timer_crc,
    ] if v])
    ev = "\n".join([dd.debounce_threshold, dd.debounce_threshold, dd.debounce_threshold])

    kwargs = {
        "Category": "UNIT",
        "Group": "CAN",
        "Test Case Name": "Fid Inhibit",
        "Test Purpose, Description": f"Message: {nm}\n"
                                     f"1) After message error occurs, verify Fid operation during Init\n",
        "Test Execution (TE) - Description": f"Init Task operation in message fault condition\n"
                                             f"IG OFF → ON\n",
        "TE-Variable": f"{te}",
        "TE-Compare": "'=",
        "TE-Value": f"{tv}",
        "Expected Results (ER) - Description": f"1) After a {nm} error occurs, initialize the Diagnostic Timer value to the timer threshold during Init operation\n",
        "ER-Variable": f"{er}",
        "ER-Compare": "'=",
        "ER-Value": f"{ev}",
        "Test Result Description": f"1) After a {nm} error occurs, initialize the Diagnostic Timer value to the timer threshold during Init operation\n" 
                                   f" - Fid operation : {dd.fid} != 128 (Inhibit)\n"
                                   f" - Init Task operation : IGN Triggered\n"
                                   f" - {dd.debounce_timer_msg} = {dd.debounce_threshold}\n"
                                   f" - {dd.debounce_timer_alv} = {dd.debounce_threshold}\n"
                                   f" - {dd.debounce_timer_crc} = {dd.debounce_threshold}\n"

    }
    kwargs.update(override)
    return UnitTestCase(**kwargs)

def error_clear(message:str, **override) -> UnitTestCase:
    """
    UNIT TEST CASE FOR CAN ERROR CLEAR
    """
    nm = naming(message)
    dd = DataDictionary()
    dd.eep_reset           = nm.eepReset
    dd.eep                 = nm.eep
    dd.diagnosis_bit_msg   = nm.diagnosisMsg
    dd.diagnosis_bit_alv   = nm.diagnosisCrc
    dd.diagnosis_bit_crc   = nm.diagnosisAlv
    dd.deve_msg            = nm.deveMsg
    dd.deve_alv            = nm.deveAlv
    dd.deve_crc            = nm.deveCrc

    # VARIABLE NAMING
    # TE-VARIABLE
    te = "\n".join([v for v in [
        "DAux_TrigClr_C",
        dd.eep_reset,
        dd.eep,
    ] if v])
    tv = "\n".join(['255 → 0', '255 → 0', '0'])

    # ER-VARIABLE
    er = "\n".join([v for v in [
        dd.diagnosis_bit_msg,
        dd.diagnosis_bit_alv,
        dd.diagnosis_bit_crc,
        dd.deve_msg,
        dd.deve_alv,
        dd.deve_crc,
    ] if v])
    ev = "\n".join(['1 → 0', '1 → 0', '1 → 0','1.6E+04 → 0','1.6E+04 → 0','1.6E+04 → 0'])

    kwargs = {
        "Category": "UNIT",
        "Group": "CAN",
        "Test Case Name": "Error Clear",
        "Test Purpose, Description": f"Message: {nm}\n"
                                     f"1) EEP Reset \n"
                                     f"2) Error Clear \n",
        "Test Execution (TE) - Description": f"1) Clear All {nm} DEve Report\n"
                                             f" - DAux_TrigClr_C = 255 → 0\n"
                                             f"2) Clear DEve Report after EEP Reset",
        "TE-Variable": f"{te}",
        "TE-Compare": "'=",
        "TE-Value": f"{tv}",
        "Expected Results (ER) - Description": f"1) When Clear the DEve Report, DEve reoccurs due to the EEP\n"
                                               f"2) After EEP Reset and Clear DEve Report, Error Clear" ,
        "ER-Variable": f"{er}",
        "ER-Compare": "'=",
        "ER-Value": f"{ev}",
        "Test Result Description": f"1) When EEP SET, Clear DTC\n" 
                                   f" - Cannot Clear DTC : Error reoccurs\n"
                                   f" - {dd.eep} = 1\n"
                                   f" - {dd.diagnosis_bit_msg} = 0 → 1\n"
                                   f" - {dd.diagnosis_bit_alv} = 0 → 1\n"
                                   f" - {dd.diagnosis_bit_crc} = 0 → 1\n"
                                   f" - {dd.deve_msg} = 0 → 1.6E+04\n"
                                   f" - {dd.deve_alv} = 0 → 1.6E+04\n"
                                   f" - {dd.deve_crc} = 0 → 1.6E+04\n"
                                   f"2) When EEP RESET, Clear DTC\n"
                                   f" - Clear DTC Successfully: Error Cleared\n"
                                   f" - {dd.eep} = 0\n"
                                   f" - {dd.diagnosis_bit_msg} = 0\n"
                                   f" - {dd.diagnosis_bit_alv} = 0\n"
                                   f" - {dd.diagnosis_bit_crc} = 0\n"
                                   f" - DFRM_DEveID_A_[] = 0\n"

    }
    kwargs.update(override)
    return UnitTestCase(**kwargs)

def clear_edr(message:str, **override) -> UnitTestCase:
    """
    UNIT TEST CASE FOR CAN CLEAR EDR ARRAY
    """
    nm = naming(message)
    dd = DataDictionary()
    dd.eep_reset           = nm.eepReset
    dd.eep                 = nm.eep
    dd.deve_msg            = nm.deveMsg
    dd.deve_alv            = nm.deveAlv
    dd.deve_crc            = nm.deveCrc

    # VARIABLE NAMING
    # TE-VARIABLE
    te = "\n".join([v for v in [
        dd.eep_reset,
        dd.eep,
    ] if v])
    tv = "\n".join(['255 → 0', '1 → 0'])

    # ER-VARIABLE
    er = "\n".join([v for v in [
        "DEve_stEDR93DTC_A[ ]",
    ] if v])
    ev = "\n".join(["refer to ER"]),

    kwargs = {
        "Category": "UNIT",
        "Group": "CAN",
        "Test Case Name": "EDR CLEAR",
        "Test Purpose, Description": f"Message: {nm}\n"
                                     f"1) When EEP RESET : CLEAR EDR \n"
                                     f"2) When EEP SET : EDR SET \n",
        "Test Execution (TE) - Description": f"1) EEP RESET\n"
                                             f" - {dd.eep_reset} : 255 → 0\n"
                                             f"2) EEP SET\n"
                                             f" - IgKey_On = True\n"
                                             f" - Message Auto-Detect and Store To EEPROM",
        "TE-Variable": f"{te}",
        "TE-Compare": "'=",
        "TE-Value": f"{tv}",
        "Expected Results (ER) - Description": f"1) When EEP RESET, Clear EDR  bit corresponding to the Deve\n"
                                               f"2) When EEP SET, Set EDR bit corresponding to the Deve" ,
        "ER-Variable": f"{er}",
        "ER-Compare": "'=",
        "ER-Value": f"{ev}",
        "Test Result Description": f"1) When EEP RESET, Clear EDR\n" 
                                   f" - {dd.eep} = 1 → 0\n"
                                   f" - DEve_stEDR93DTC_A[Array_id].BitPosn = 1 → 0\n"
                                   f" - Array_id = DFC_id / 16\n"
                                   f" - BitPosn = DFC_id % 16\n"
                                   f" - DFC_id : Check the DSMDOC file\n"

                                   f"2) When EEP SET, Set EDR\n"
                                   f" - {dd.eep} = 0 → 1\n"
                                   f" - DEve_stEDR93DTC_A[Array_id].BitPosn = 1 → 0\n"
                                   f" - Array_id = DFC_id / 16\n"
                                   f" - BitPosn = DFC_id % 16\n"
                                   f" - DFC_id : Check the DSMDOC file\n"
    }
    kwargs.update(override)
    return UnitTestCase(**kwargs)


if __name__ == "__main__":


    # md = Amd(r"E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\CANInterface\ABS\MessageDiag\CanFDABSD\CanFDABSD.zip")
    # vr = md.main.dataframe('Element')["name"]
    # det = detection("ABS_ESC_01_10ms", vr)

    det = detection("ABS_ESC_01_10ms")
    alive = diagnosis_alive("ABS_ESC_01_10ms")
    crc = diagnosis_crc("ABS_ESC_01_10ms"),
    fid = fid_inhibit("ABS_ESC_01_10ms")
    clear = error_clear("ABS_ESC_01_10ms")
    print(det)
    print(alive)
    print(clear)

