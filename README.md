# cannect

---

<b>HKMG/EMS ASW 편의 도구</b><br>
본 프레임워크는 EMS/ASW 개발의 특수한 목적을 위해 제작되었으며 허용된 호스트 도메인에서만 작동합니다. 본 프레임워크는 허용된 호스트 도메인의 리소스에 대한 개발 및 검증 편의도구를 제공하며 리소스는 보안 정책에 따라 외부로 반출할 수 없습니다. 이를 위반하여 사용자가 리소스를 외부로 무단 반출 또는 반출 시도 시 관련 법률 및 보안 정책에 의거 불이익 또는 처벌을 받을 수 있습니다.<br><br>
<i>Developed and Powered by</i> <b>HYUNDAI KEFICO Co.,Ltd.</b>

---

# 사용자 가이드
## 1. 리소스 경로 설정 (선택)

모든 리소스는 호스트 도메인의 저장소 및 SVN을 참조합니다. 필요에 따라 사용자는 로컬 환경에 Check-Out된 SVN을 사용할 수 있습니다. 이 경우, 아래 예시에 따라 로컬 SVN 경로를 적용하여야 합니다. 
사용 시 스크립트 실행 마다 또는 커널 최초 실행 시 적용되어야 합니다.
 
```commandline
예시) 

from cannect import env, mount # env는 환경 변수

print(env.SVN)      # 기본 SVN 경로 사용 
mount(r"E:\SVN")    # 사용자 Local의 SVN 최상위 경로를 입력, 매 코드 실행 시 최상단에 입력
print(env.SVN)
```
```commandline
결과)

\\kefico\ --- {세부 경로 보안 처리} --- \SVN
E:\SVN
```

## 2. 통신 개발
통신 모듈에는 자동 ASCET 모델 생성용 AscetCAN과 CAN DB에 관한 일체 기능을 담당하는 DataBaseCAN 모듈이 있습니다.

### 2.1. DataBaseCAN
```text
모듈 구조)

├── DataBaseCAN
│   ├── Reader(src) --------------------------------- (C) CAN DB(SPEC) 읽기 
│   │   ├── db                                      : └─ attribute; [DataFrame] 원본 데이터프레임
│   │   ├── source                                  : └─ attribute; [str] DB json 파일 전체 경로
│   │   ├── traceability                            : └─ attribute; [str] DB json 파일 이름
│   │   ├── revision                                : └─ attribute; [str] DB Excel 파일 Revision @수정 번호
│   │   ├── messages                                : └─ @property; [DataDictionary[메시지 이름, 메시지 객체]
│   │   ├── signals                                 : └─ @property; [DataDictionary[신호 이름, 신호 객체]
│   │   ├── mode(engine_spec)                       : └─ method; "HEV", "ICE" 사양에 대한 DB
│   │   ├── is_developer_mode()                     : └─ method; 개발자 모드 여부
│   │   ├── is_dbc(engine_spec, channel, **kwargs)  : └─ method; 개발자 모드 여부
│   │   └── to_developer_mode(engine_spec)          : └─ method; 개발자 모드로 전환
│   │
│   ├── Specification(db) --------------------------- (C) 사양서 제작                          
│   │   └── generate(filename)                      : └─ method; 사양서 제작, 다운로드 경로에 생성
│   │
└── └── VersionControl(filename) -------------------- (C) CAN DB(SPEC) 버전 관리
        ├── name                                    : └─ attribute; DB 파일 이름 (확장자 제외)
        ├── filename                                : └─ attribute; DB 파일 이름 (확장자 포함)
        ├── filepath                                : └─ attribute; DB 파일 경로 (전체 경로)
        ├── history                                 : └─ attribute; DB 파일 SVN 이력
        ├── revision                                : └─ attribute; DB 파일 최신 SVN Revision
        ├── json                                    : └─ @property; .revision에 해당하는 json 파일(전체 경로)
        ├── commit_json()                           : └─ method; # TODO
        └── to_json(mode)                           : └─ method; 사양서 제작, 다운로드 경로에 생성
```

#### 2.1.1. DataBaseCAN.Reader

CAN DB 읽기 클래스입니다.<br>
<i><span style="color:green">:param</span></i> src: [str] CAN SPEC(DB)의 .json 파일 전체 경로

```commandline
예시) 

from cannect import DataBaseCAN

db = DataBaseCAN.Reader(src='')
# 특정 프로젝트(G-프로젝트 등)를 위한 DB를 사용할 경우 json 파일 형식의 데이터를 @src에 사용
# 미적용 시 SVN 내 최신 DB 사용
print(db)
print(db.source)       # json 파일 전체 경로
print(db.traceability) # 원본 DB 이름 (json 파일명)
print(db.revision)     # 원본 DB의 SVN Revision 및 로컬 재생성 횟수
```

```commandline
결과
          ECU          Message     ID  DLC Send Type  Cycle Time                 Signal                                         Definition  Length  StartBit           Sig Receivers UserSigValidity                                        Value Table Value Type GenSigStartValue  Factor  Offset  Min   Max Unit Local Network Wake Up Request Network Request Holding Time                                        Description   Version Requirement ID Required Date                                             Remark    Status ByteOrder ICE Channel ICE WakeUp HEV Channel HEV WakeUp        SystemConstant           Codeword   Formula SignedProcessing    InterfacedVariable SignalRenamed
0     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10        ABS_ESC_Crc1Val                ABS_ESC_CyclicRedundancyCheck1Value      16         0      AWD,EMS,TCU,SCU_FF             IG1                                0x0~0xFFFF:CRCValue   Unsigned           0xFFFF     1.0     0.0  0.0   0.0                                 No                            0  "The data area for CRC calculation is based on...  21.09.03                                                                                  Official     Intel           P                      P                                                      OneToOne                             //Internal              
1     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10     ABS_ESC_AlvCnt1Val                         ABS_ESC_AliveCounter1Value       8        16      AWD,EMS,TCU,SCU_FF             IG1                               0x0~0xFF:AlvCntValue   Unsigned              0x0     1.0     0.0  0.0   0.0                                 No                            0  "For the first transmission request for a data...  21.09.03                                                                                  Official     Intel           P                      P                                                      OneToOne                             //Internal              
2     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10         ABS_WrngLmpSta  ABS_WarningLampStatus ##2G##ESC - TCS15 - ABS_...       2        24          AWD,TCU,SCU_FF             IG1  0x0:ABS Warning lamp OFF/0x1:ABS Warning lamp ...   Unsigned              0x0     1.0     0.0  0.0   0.0                                 No                            0  The signal indicates the status of the ABS War...  19.07.02                                                                                  Official     Intel                                  P                                                      OneToOne                        FD_stAbsWrngLmp                            
...       ...              ...    ...  ...       ...         ...                    ...                                                ...     ...       ...                     ...             ...                                                ...        ...              ...     ...     ...  ...   ...  ...                           ...                          ...                                                ...       ...            ...           ...                                                ...       ...       ...         ...        ...         ...        ...                   ...                ...       ...              ...                   ...           ...         
1791      EMS      EMS_LDCBMS1  0x52C    8         P          50          CF_Ems1_Alive                                                          2        54                     LDC             IG1                                                      unsigned              0x0     0.0     0.0  0.0   3.0                                 No                            0                                                     19.06.25                               "'2025.07.02. 자체 DB 개정\n- 현재 EMS 송출 중이나, 수신처 없...  Official     Intel           L                                    MICROEPT_48V_SC == 1  Cfg_MeptSys_C > 0                              //Internal              
1792      EMS      EMS_LDCBMS1  0x52C    8         P          50        CF_stDesModDcdc                                                          4        56                     LDC             IG1  0x0:Init (wake-up)/0x5:Idle / Neutral/0x8:Forw...   unsigned              0x0     0.0     0.0  0.0  15.0                                 No                            0                  Desired LDC operation mode by EMS  19.06.25                               "'2025.07.02. 자체 DB 개정\n- 현재 EMS 송출 중이나, 수신처 없...  Official     Intel           L                                    MICROEPT_48V_SC == 1  Cfg_MeptSys_C > 0                            Ldc_stDesMod              
1793      EMS      EMS_LDCBMS1  0x52C    8         P          50         CF_Ems1_ChkSum                                                          4        60                     LDC             IG1     0x0:No error/0x1:Engine speed sensor defective   unsigned              0x0     0.0     0.0  0.0  15.0                                 No                            0  "This signal indicates Checksum for robustness...  19.06.25                               "'2025.07.02. 자체 DB 개정\n- 현재 EMS 송출 중이나, 수신처 없...  Official     Intel           L                                    MICROEPT_48V_SC == 1  Cfg_MeptSys_C > 0                              //Internal              

[1794 rows x 39 columns]
E:\SVN\dev.bsw\ --- {세부 경로 보안 처리} --- \자체제어기_KEFICO-EMS_CANFD_r21713@03.json
자체제어기_KEFICO-EMS_CANFD_r21713@03
r21713@03
```

사양서 제작 시에는 엔진 사양 별 DB를 재구성해서 사용합니다.
```commandline
예시)

db_hev = db.mode(engine_spec="HEV")
db_ice = db.mode(engine_spec="ICE")
print(db_hev)
print(db_ice)

```
```commandline
결과)

          ECU          Message     ID  DLC Send Type  Cycle Time                      Signal                                         Definition  Length  StartBit           Sig Receivers UserSigValidity                                        Value Table Value Type GenSigStartValue    Factor     Offset        Min         Max  Unit Local Network Wake Up Request Network Request Holding Time                                        Description   Version Requirement ID Required Date Remark    Status ByteOrder ICE Channel ICE WakeUp HEV Channel HEV WakeUp SystemConstant Codeword   Formula SignedProcessing       InterfacedVariable        SignalRenamed
0     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10             ABS_ESC_Crc1Val                ABS_ESC_CyclicRedundancyCheck1Value      16         0      AWD,EMS,TCU,SCU_FF             IG1                                0x0~0xFFFF:CRCValue   Unsigned           0xFFFF  1.000000   0.000000   0.000000    0.000000                                  No                            0  "The data area for CRC calculation is based on...  21.09.03                                      Official     Intel           P                      P                                     OneToOne                                //Internal                     
1     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10          ABS_ESC_AlvCnt1Val                         ABS_ESC_AliveCounter1Value       8        16      AWD,EMS,TCU,SCU_FF             IG1                               0x0~0xFF:AlvCntValue   Unsigned              0x0  1.000000   0.000000   0.000000    0.000000                                  No                            0  "For the first transmission request for a data...  21.09.03                                      Official     Intel           P                      P                                     OneToOne                                //Internal                     
2     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10              ABS_WrngLmpSta  ABS_WarningLampStatus ##2G##ESC - TCS15 - ABS_...       2        24          AWD,TCU,SCU_FF             IG1  0x0:ABS Warning lamp OFF/0x1:ABS Warning lamp ...   Unsigned              0x0  1.000000   0.000000   0.000000    0.000000                                  No                            0  The signal indicates the status of the ABS War...  19.07.02                                      Official     Intel                                  P                                     OneToOne                           FD_stAbsWrngLmp                     
...       ...              ...    ...  ...       ...         ...                         ...                                                ...     ...       ...                     ...             ...                                                ...        ...              ...       ...        ...        ...         ...   ...                           ...                          ...                                                ...       ...            ...           ...    ...       ...       ...         ...        ...         ...        ...            ...      ...       ...              ...                      ...                  ...
1752      EMS    LEMS_09_100ms  0x261    8         P         100    CLU_LoFuelWrngSta_Copy_1                           CLU_LowFuelWarningStatus       2        16               TCU,Dummy             IG1  0x0:Low fuel Warning is off/0x1:Low fuel Warni...   Unsigned              0x0  1.000000   0.000000   0.000000    3.000000                                  No                            0                                                     19.03.05                                      Official     Intel                                  L                                                                  CLU_LoFuelWrngSta_Can    CLU_LoFuelWrngSta
1753      EMS    LEMS_09_100ms  0x261    8         P         100  DATC_OutTempSnsrVal_Copy_1                 DATC_OutsideTemperatureSensorValue       8        18               TCU,Dummy             IG1                                         0xFF:Error   Unsigned              0x0  0.500000 -40.000000 -40.000000   87.500000  degC                            No                            0                                                     19.03.05                                      Official     Intel                                  L                                                                DATC_OutTempSnsrVal_Can  DATC_OutTempSnsrVal
1754      EMS    LEMS_09_100ms  0x261    8         P         100        ICU_BS1BatVol_Copy_1  Actual battery voltage by battery sensor. ##2G...       8        26               TCU,Dummy             IG1                               0xFF:Error indicator   Unsigned              0x0  0.101562   0.000000   0.000000   25.898000     V                            No                            0                                                     19.03.05                                      Official     Intel                                  L                                                                               BattU_u8       HEV_BattVolVal

[799 rows x 39 columns]

          ECU          Message     ID  DLC Send Type  Cycle Time                 Signal                                         Definition  Length  StartBit           Sig Receivers UserSigValidity                                        Value Table Value Type GenSigStartValue  Factor  Offset  Min   Max Unit Local Network Wake Up Request Network Request Holding Time                                        Description   Version Requirement ID Required Date                                             Remark    Status ByteOrder ICE Channel ICE WakeUp HEV Channel HEV WakeUp        SystemConstant           Codeword   Formula SignedProcessing    InterfacedVariable SignalRenamed
0     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10        ABS_ESC_Crc1Val                ABS_ESC_CyclicRedundancyCheck1Value      16         0      AWD,EMS,TCU,SCU_FF             IG1                                0x0~0xFFFF:CRCValue   Unsigned           0xFFFF     1.0     0.0  0.0   0.0                                 No                            0  "The data area for CRC calculation is based on...  21.09.03                                                                                  Official     Intel           P                      P                                                      OneToOne                             //Internal              
1     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10     ABS_ESC_AlvCnt1Val                         ABS_ESC_AliveCounter1Value       8        16      AWD,EMS,TCU,SCU_FF             IG1                               0x0~0xFF:AlvCntValue   Unsigned              0x0     1.0     0.0  0.0   0.0                                 No                            0  "For the first transmission request for a data...  21.09.03                                                                                  Official     Intel           P                      P                                                      OneToOne                             //Internal              
3     CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10           ABS_DfctvSta    ABS_DefectiveStatus ##2G##ESC - TCS11 - ABS_DEF       2        26  AWD,EMS,TCU,LSD,SCU_FF             IG1  0x0:ABS is not defective/0x1:ABS is defective/...   Unsigned              0x0     1.0     0.0  0.0   0.0                                 No                            0  Information regarding the ABS defective indica...  19.07.02                                                                                  Official     Intel           P                      P                                                      OneToOne                          FD_stAbsDfctv              
...       ...              ...    ...  ...       ...         ...                    ...                                                ...     ...       ...                     ...             ...                                                ...        ...              ...     ...     ...  ...   ...  ...                           ...                          ...                                                ...       ...            ...           ...                                                ...       ...       ...         ...        ...         ...        ...                   ...                ...       ...              ...                   ...           ...              
1791      EMS      EMS_LDCBMS1  0x52C    8         P          50          CF_Ems1_Alive                                                          2        54                     LDC             IG1                                                      unsigned              0x0     0.0     0.0  0.0   3.0                                 No                            0                                                     19.06.25                               "'2025.07.02. 자체 DB 개정\n- 현재 EMS 송출 중이나, 수신처 없...  Official     Intel           L                                    MICROEPT_48V_SC == 1  Cfg_MeptSys_C > 0                                       //Internal              
1792      EMS      EMS_LDCBMS1  0x52C    8         P          50        CF_stDesModDcdc                                                          4        56                     LDC             IG1  0x0:Init (wake-up)/0x5:Idle / Neutral/0x8:Forw...   unsigned              0x0     0.0     0.0  0.0  15.0                                 No                            0                  Desired LDC operation mode by EMS  19.06.25                               "'2025.07.02. 자체 DB 개정\n- 현재 EMS 송출 중이나, 수신처 없...  Official     Intel           L                                    MICROEPT_48V_SC == 1  Cfg_MeptSys_C > 0                                     Ldc_stDesMod              
1793      EMS      EMS_LDCBMS1  0x52C    8         P          50         CF_Ems1_ChkSum                                                          4        60                     LDC             IG1     0x0:No error/0x1:Engine speed sensor defective   unsigned              0x0     0.0     0.0  0.0  15.0                                 No                            0  "This signal indicates Checksum for robustness...  19.06.25                               "'2025.07.02. 자체 DB 개정\n- 현재 EMS 송출 중이나, 수신처 없...  Official     Intel           L                                    MICROEPT_48V_SC == 1  Cfg_MeptSys_C > 0                                       //Internal              

[1336 rows x 39 columns]
```

dbc 파일을 제작할 수 있습니다. @engine_spec과 @channel 입력 시 메시지(ID) 중복 없이 해당 채널에 대한 .dbc 파일을 생성합니다.<br>
이 때 채널에 <span style="color:indianred;">ID가 중복</span>되는 경우, <span style="color:indianred;">{Codeword}나 {SystemConstant}를 명시적으로 구분</span>하여야 합니다.

```commandline
예시) 

db.to_dbc(engine_spec="ICE", channel=1)                                     # CANDBDuplicationError 발생: 중복 ID
db.to_dbc(engine_spec="ICE", channel=1, Codeword="Cfg_CanFDSTDDB_C == 0")   # 중복 제거를 위한 사양 명시
```

```commandline
결과)

# 별도 출력 없음; Downloads 폴더에 {engine_spec}-{CAN채널}-{명시된 사양}.dbc 파일로 자동 저장
```

.to_developer_mode(engine_spec)는 동일 메시지의 채널 분기 등 예외적 상황을 위한 DB 변환 모드입니다. 자동 모델 생성, Test Case 생성 등에 사용합니다. 
필요에 따라 .is_developer_mode()를 선행적으로 확인한 후 중복해서 모드 변환을 하지 않도록 주의합니다.

```commandline
예시)

db_dev = db.to_developer_mode("HEV")
print(db_dev)
```

```commandline
결과)

         ECU          Message     ID  DLC Send Type  Cycle Time              Signal                                         Definition  Length  StartBit           Sig Receivers UserSigValidity                                        Value Table Value Type GenSigStartValue  Factor  Offset  Min  Max Unit Local Network Wake Up Request Network Request Holding Time                                        Description   Version Requirement ID Required Date Remark    Status ByteOrder ICE Channel ICE WakeUp HEV Channel HEV WakeUp SystemConstant Codeword   Formula SignedProcessing      InterfacedVariable SignalRenamed Channel WakeUp
0    CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10     ABS_ESC_Crc1Val                ABS_ESC_CyclicRedundancyCheck1Value      16         0      AWD,EMS,TCU,SCU_FF             IG1                                0x0~0xFFFF:CRCValue   Unsigned           0xFFFF     1.0     0.0  0.0  0.0                                 No                            0  "The data area for CRC calculation is based on...  21.09.03                                      Official     Intel           P                      P                                     OneToOne                               //Internal                     P       
1    CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10  ABS_ESC_AlvCnt1Val                         ABS_ESC_AliveCounter1Value       8        16      AWD,EMS,TCU,SCU_FF             IG1                               0x0~0xFF:AlvCntValue   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0  "For the first transmission request for a data...  21.09.03                                      Official     Intel           P                      P                                     OneToOne                               //Internal                     P       
2    CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10      ABS_WrngLmpSta  ABS_WarningLampStatus ##2G##ESC - TCS15 - ABS_...       2        24          AWD,TCU,SCU_FF             IG1  0x0:ABS Warning lamp OFF/0x1:ABS Warning lamp ...   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0  The signal indicates the status of the ABS War...  19.07.02                                      Official     Intel                                  P                                     OneToOne                          FD_stAbsWrngLmp                     P       
..       ...              ...    ...  ...       ...         ...                 ...                                                ...     ...       ...                     ...             ...                                                ...        ...              ...     ...     ...  ...  ...  ...                           ...                          ...                                                ...       ...            ...           ...    ...       ...       ...         ...        ...         ...        ...            ...      ...       ...              ...                     ...           ...     ...    ...       
958      EMS    EMS_15_H_00ms  0x300   32        EW           0      ImmoConf_HEV_H                       HEV_ImmobilizerConfiguration       2        72                     VPC             IG1  0x0:Non Immobilizer/0x1:Immobilizer/0x2:Not us...   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0                          Immobilizer Configuration  19.05.05                                      Official     Intel                                P,H                                                                 ImHev_cImobMod_(P, H)                     H       
959      EMS    EMS_15_H_00ms  0x300   32        EW           0       EngLock_HEV_H                                     HEV_EngineLock       2        74                     VPC             IG1  0x0:Engine Unlock/0x1:Engine Lock/0x2:Not used...   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0                            Engine Lock Information  19.05.05                                      Official     Intel                                P,H                                                                 ImHev_cEmsLock_(P, H)                     H       
960      EMS    EMS_15_H_00ms  0x300   32        EW           0     AuthCount_HEV_H                            HEV_AuthenticationCount       4        76                     VPC             IG1                                                      Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0                               Authentication Count  19.05.05                                      Official     Intel                                P,H                                                                   ImHev_ctAuth_(P, H)                     H       

[870 rows x 41 columns]
```

클래스의 인스턴스는 __getitem__을 지원합니다. 기본적으로 pandas의 DataFrame.__getitem__을 상속하여 사용합니다. 필요에 따라 DB를 가공하여 자동화 모델, Test Case 생성 등에 사용합니다.

```commandline
예시)

print(db[db["ECU"] != "EMS"])                   # EMS 기준, 수신 제어기만 선택
print(db[db["ICE Channel"].str.contains("P")])  # ICE 사양의 P-CAN 메시지만 선택
```

```commandline
결과)

         ECU          Message     ID  DLC Send Type  Cycle Time              Signal                                         Definition  Length  StartBit                                      Sig Receivers UserSigValidity                                        Value Table Value Type GenSigStartValue   Factor  Offset  Min  Max  Unit Local Network Wake Up Request Network Request Holding Time                                        Description   Version Requirement ID Required Date Remark    Status ByteOrder ICE Channel ICE WakeUp HEV Channel HEV WakeUp SystemConstant Codeword         Formula SignedProcessing InterfacedVariable SignalRenamed
0    CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10     ABS_ESC_Crc1Val                ABS_ESC_CyclicRedundancyCheck1Value      16         0                                 AWD,EMS,TCU,SCU_FF             IG1                                0x0~0xFFFF:CRCValue   Unsigned           0xFFFF  1.00000     0.0  0.0  0.0                                  No                            0  "The data area for CRC calculation is based on...  21.09.03                                      Official     Intel           P                      P                                           OneToOne                          //Internal              
1    CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10  ABS_ESC_AlvCnt1Val                         ABS_ESC_AliveCounter1Value       8        16                                 AWD,EMS,TCU,SCU_FF             IG1                               0x0~0xFF:AlvCntValue   Unsigned              0x0  1.00000     0.0  0.0  0.0                                  No                            0  "For the first transmission request for a data...  21.09.03                                      Official     Intel           P                      P                                           OneToOne                          //Internal              
2    CGW_CCU  ABS_ESC_01_10ms  0x06F    8         P          10      ABS_WrngLmpSta  ABS_WarningLampStatus ##2G##ESC - TCS15 - ABS_...       2        24                                     AWD,TCU,SCU_FF             IG1  0x0:ABS Warning lamp OFF/0x1:ABS Warning lamp ...   Unsigned              0x0  1.00000     0.0  0.0  0.0                                  No                            0  The signal indicates the status of the ABS War...  19.07.02                                      Official     Intel                                  P                                           OneToOne                     FD_stAbsWrngLmp                            
..       ...              ...    ...  ...       ...         ...                 ...                                                ...     ...       ...                                                ...             ...                                                ...        ...              ...      ...     ...  ...  ...   ...                           ...                          ...                                                ...       ...            ...           ...    ...       ...       ...         ...        ...         ...        ...            ...      ...             ...              ...                ...           ...
954  CGW_CCU      WHL_01_10ms  0x0A0   24         P          10        WHL_SpdFRVal  WHL_SpeedFrontRightValue ##2G##ESC - WHL_SPD11...      14        80  AWD,EMS,TCU,OPU,LSD,SCU_FF,WCCU,EVSCU_FF,VDU,A...             IG1                                       0x3FFF:Error   Unsigned              0x0  0.03125     0.0  0.0  0.0  km/h                            No                            0  "This signal provides the wheel velocity of ea...  17.12.00                                      Official     Intel           P                                                            V_kph_q0p03125                   WHEEL_FR_WHL_Intf              
955  CGW_CCU      WHL_01_10ms  0x0A0   24         P          10        WHL_SpdRLVal  WHL_SpeedRearLeftValue ##2G##ESC - WHL_SPD11 -...      14        96  AWD,EMS,TCU,OPU,LSD,SCU_FF,EVSCU_FF,VDU,ALDC,V2LC             IG1                                       0x3FFF:Error   Unsigned              0x0  0.03125     0.0  0.0  0.0  km/h                            No                            0  "This signal provides the wheel velocity of ea...  17.12.00                                      Official     Intel           P                                                            V_kph_q0p03125                   WHEEL_RL_WHL_Intf              
956  CGW_CCU      WHL_01_10ms  0x0A0   24         P          10        WHL_SpdRRVal  WHL_SpeedRearRightValue ##2G##ESC - WHL_SPD11 ...      14       112  AWD,EMS,TCU,OPU,LSD,SCU_FF,EVSCU_FF,VDU,ALDC,V2LC             IG1                                       0x3FFF:Error   Unsigned              0x0  0.03125     0.0  0.0  0.0  km/h                            No                            0  "This signal provides the wheel velocity of ea...  17.12.00                                      Official     Intel           P                                                            V_kph_q0p03125                   WHEEL_RR_WHL_Intf              

[957 rows x 39 columns]
          ECU           Message     ID  DLC Send Type  Cycle Time              Signal                                         Definition  Length  StartBit           Sig Receivers UserSigValidity                                        Value Table Value Type GenSigStartValue  Factor  Offset  Min  Max Unit Local Network Wake Up Request Network Request Holding Time                                        Description   Version               Requirement ID Required Date Remark    Status ByteOrder ICE Channel ICE WakeUp HEV Channel HEV WakeUp SystemConstant       Codeword   Formula SignedProcessing            InterfacedVariable SignalRenamed
0     CGW_CCU   ABS_ESC_01_10ms  0x06F    8         P          10     ABS_ESC_Crc1Val                ABS_ESC_CyclicRedundancyCheck1Value      16         0      AWD,EMS,TCU,SCU_FF             IG1                                0x0~0xFFFF:CRCValue   Unsigned           0xFFFF     1.0     0.0  0.0  0.0                                 No                            0  "The data area for CRC calculation is based on...  21.09.03                                                    Official     Intel           P                      P                                           OneToOne                                     //Internal              
1     CGW_CCU   ABS_ESC_01_10ms  0x06F    8         P          10  ABS_ESC_AlvCnt1Val                         ABS_ESC_AliveCounter1Value       8        16      AWD,EMS,TCU,SCU_FF             IG1                               0x0~0xFF:AlvCntValue   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0  "For the first transmission request for a data...  21.09.03                                                    Official     Intel           P                      P                                           OneToOne                                     //Internal              
3     CGW_CCU   ABS_ESC_01_10ms  0x06F    8         P          10        ABS_DfctvSta    ABS_DefectiveStatus ##2G##ESC - TCS11 - ABS_DEF       2        26  AWD,EMS,TCU,LSD,SCU_FF             IG1  0x0:ABS is not defective/0x1:ABS is defective/...   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0  Information regarding the ABS defective indica...  19.07.02                                                    Official     Intel           P                      P                                           OneToOne                                  FD_stAbsDfctv                            
...       ...               ...    ...  ...       ...         ...                 ...                                                ...     ...       ...                     ...             ...                                                ...        ...              ...     ...     ...  ...  ...  ...                           ...                          ...                                                ...       ...                          ...           ...    ...       ...       ...         ...        ...         ...        ...            ...            ...       ...              ...                           ...           ...
1632      EMS    PT_OBM_02_00ms  0x516   32        EC           0  PT_OBM_AlvCnt02Val                         PT_OBM_AliveCounter02Value       8        16                  vDummy              B+                               0x0~0xFF:AlvCntValue   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0  "For the first transmission request for a data...  25.07.02  VCDM CR10783438, CR10783437    2025-09-10              TSW     Intel           P                      P               OBM_SC == 1  Cfg_OBM_C > 0                                               //Internal              
1633      EMS    PT_OBM_02_00ms  0x516   32        EC           0      OBM_Master_ECU                    OBM data trasmission Controller       3        24                  CCU_AP             IG1  0x0:Default/0x1:EMS (ECU ID : 7E0)/0x2:VCU/VPC...   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0  This signal shows which controller transmits t...  25.07.04  VCDM CR10783438, CR10783437    2025-09-10              TSW     Intel           P                      P               OBM_SC == 1  Cfg_OBM_C > 0                                                     상수 1              
1634      EMS    PT_OBM_02_00ms  0x516   32        EC           0   OBM_Outbox_Status                                  OBM Outbox Status       3        27                  CCU_AP             IG1            0x0:Default/0x1:Request/0x2:Success ACK   Unsigned              0x0     1.0     0.0  0.0  0.0                                 No                            0  This signal shows OBM Outbox Status from Data ...  25.07.04  VCDM CR10783438, CR10783437    2025-09-10              TSW     Intel           P                      P               OBM_SC == 1  Cfg_OBM_C > 0                                               OBM_TraReq              

[967 rows x 39 columns]
```

#### 2.1.2. DataBaseCAN.Specification

DB에 대한 사양서(구 SDD) 제작 클래스입니다.<br>
<i><span style="color:green">:param</span></i> db: DataBaseCAN.Reader.mode의 객체

```commandline
예시)

# 아래와 같이 실행 시, 사용자\다운로드 경로에 {filename}.docx로 생성
spec = DataBaseCAN.Specification(db)
spec.generate(filename)              # filename 필수 입력
```

#### 2.1.3. DataBaseCAN.VersionControl

SVN/엑셀 DB에 대한 json 파일 생성 및 버전 관리 클래스입니다.<br>
관리자의 엑셀 CAN DB에 대한 버전 및 소스 관리를 수행합니다.<br>
<i><span style="color:green">:param</span></i> filename: str, SVN/.../CAN_Database 경로에 위치한 엑셀 파일 이름, 미입력 시 자체제어기 DB 선택<br><br>
<span style="color:indianred;">DB@SVN revision에 대한 json이 없는 경우 오류가 표출되므로 선행적 생성 필요</span>

```commandline
예시)

vc = DataBaseCAN.VersionControl()
print(vc.name)          # DB 파일 이름 (확장자 제외)
print(vc.filename)      # DB 파일 이름 (확장자 포함)
print(vc.revision)      # DB 파일 최신 SVN Revision
print(vc.filepath)      # DB 파일 경로 (전체 경로)
print(vc.json)          # .revision에 해당하는 json 파일(전체 경로)
print(vc.history)       # DB 파일 SVN 이력
```

```commandline
결과)

자체제어기_KEFICO-EMS_CANFD
자체제어기_KEFICO-EMS_CANFD.xlsx
r21725
\\kefico\ --- {세부 경로 보안 처리} --- \CAN_Database\자체제어기_KEFICO-EMS_CANFD.xlsx
\\kefico\ --- {세부 경로 보안 처리} --- \CAN_Database\dev\자체제어기_KEFICO-EMS_CANFD_r21725@01.json
   revision         author             datetime                                                            log
0    r21725  ZS25282@AUTOS  2026-01-30 11:54:41                                        MCU P-CAN channel added
1    r21715  ZS19577@AUTOS  2026-01-29 11:02:24                                                 [J**H*****.Jo]
2    r21714  ZS19577@AUTOS  2026-01-29 10:09:13                                                 [J**H*****.Jo]
..      ...            ...                  ...                                                            ...
82   r21190  ZS19542@AUTOS  2024-08-09 13:30:17                          ESC_06_200ms@HEV 삭제(LCR 요구사항 번복)
83   r21189  ZS19542@AUTOS  2024-08-09 13:28:52  ESC_01_10ms@HEV P,H 채널 중복 수신에서 P 채널 단일 수신으로 변경...
84   r21179  ZS19542@AUTOS  2024-08-09 13:13:05                                                        최초 적용

[79 rows x 4 columns]
```

### 2.2. AscetCAN
```text
모듈 구조)

├── AscetCAN
│   ├── ComDef(db, engine_spec, base_model, exclude_tsw) --- (C) ComDef 모델 생성
│   │   └── generate()                                     : └─ method;
│   │
│   ├── ComRx(db, engine_spec, base_model) ----------------- (C) ComRx 모델 생성                          
│   │   └── generate()                                     : └─ method;
│   │
└── └── ComDiag(db, base_model, *messages) ----------------- (C) 진단 모델 생성
        └── generate()                                     : └─ method;
```

#### 2.2.1. AscetCAN.ComDef

지정 경로(사용자\다운로드)에 ComDef* 모델을 생성합니다. ICE, HEV, G프로젝트 등 목적별로 구분하여 사용할 수 있습니다. base_model을 입력하지 않으면 SVN의 모델을 사용합니다.
CAN DB를 입력하면 송출처가 EMS인 경우는 자동으로 제외하며 로컬 통신 대상인 "CVVD", "48V 사양", "NOx센서"은 자동으로 제외합니다. <br>
<i><span style="color:green">:param</span></i> db: [DataBaseCAN.Reader] <br>
<i><span style="color:green">:param</span></i> engine_spec: [str] "ICE" 또는 "HEV"만 입력 가능합니다.<br> 
<i><span style="color:green">:param</span></i> base_model: [str] 베이스로 사용할 ComDef* 모델의 전체 경로를 입력합니다. 공란 입력 시 SVN 상 모델을 사용합니다. 기본 값은 미입력 공란입니다.<br>
<i><span style="color:green">:param</span></i> exclude_tsw: [bool] 모델 생성 시 BSW 참조를 무력화(255)합니다. CAN DB상 메시지가 TSW 상태로 표기되어 있어야 합니다.

```commandline
예시)

model = AscetCAN.ComDef(DataBaseCAN.Reader(), "HEV")
model.generate()
```

```commandline
결과) (생성 로그)

2026-02-03 08:44:52 %ComDef_HEV MODEL GENERATION
2026-02-03 08:44:52 >>> Engine Spec : HEV
2026-02-03 08:44:52 >>> Base Model  : \\ ... \NetworkDefinition\ComDef_HEV\ComDef_HEV.zip
2026-02-03 08:44:52 >>> DB Revision : r21727@01
2026-02-03 08:44:52 >>> Exclude TSW : Yes
2026-02-03 08:44:52 >>> Collecting Base Model Properties... 0.01s
2026-02-03 08:44:57 >>> Defining Message Elements... 4.04s
2026-02-03 08:44:58 >>> Defining Signal Elements... 1.11s
2026-02-03 08:45:00 >>> Summary
           Method Element              
            Total   Total Added Deleted
Base Model     66    1194     -      50
 New Model     68    1232    88       -
* Added: GCU_InvtTempVal_H_Can, FD_cVldMcu01HAlv, ... , GCU_ActlHsgRotatSpdRpmVal_P_Can
* Deleted: MCU_EstMtrTqPcVal_Can, Can_tiFltMcu02_C, ... , GCU_AlvCnt2ValCalc
```

#### 2.2.2. AscetCAN.ComRx

지정 경로(사용자\다운로드)에 ComRx* 모델을 생성합니다. ICE, HEV, G프로젝트 등 목적별로 구분하여 사용할 수 있습니다. base_model을 입력하지 않으면 SVN의 모델을 사용합니다.
CAN DB를 입력하면 송출처가 EMS인 경우는 자동으로 제외하며 로컬 통신 대상인 "CVVD", "48V 사양", "NOx센서"은 자동으로 제외합니다. <br>
<i><span style="color:green">:param</span></i> db: [DataBaseCAN.Reader] <br>
<i><span style="color:green">:param</span></i> engine_spec: [str] "ICE" 또는 "HEV"만 입력 가능합니다.<br> 
<i><span style="color:green">:param</span></i> base_model: [str] 베이스로 사용할 ComDef* 모델의 전체 경로를 입력합니다. 공란 입력 시 SVN 상 모델을 사용합니다. 기본 값은 미입력 공란입니다.<br>

```commandline
예시)

model = AscetCAN.ComRx(DataBaseCAN.Reader(), "HEV")
model.generate()
```

```commandline
결과) (생성 로그)

2026-02-03 08:46:47 %ComRx_HEV MODEL GENERATION
2026-02-03 08:46:47 >>> Engine Spec : HEV
2026-02-03 08:46:47 >>> Base Model  : \\ ... \MessageReceive\ComRx_HEV\ComRx_HEV.zip
2026-02-03 08:46:47 >>> DB Revision : r21727@01
2026-02-03 08:46:47 >>> Summary
           Message              
             Total Added Deleted
Base Model      66     -       2
 New Model      68     4       -
* Added: MCU_02_P_10ms, MCU_01_P_10ms, MCU_01_H_10ms, MCU_02_H_10ms
* Deleted: MCU_02_10ms, MCU_01_10ms
```

#### 2.2.3. AscetCAN.ComDiag

지정 경로(사용자\다운로드)에 CAN 진단 모델을 생성합니다. base_model의 전체 경로 또는 모델의 이름을 입력합니다. 모델 이름만 입력 시, SVN 상 모델을 참조합니다.
해당 모델에 진단하고자 하는 메시지 이름을 입력합니다. (필수)
<i><span style="color:green">:param</span></i> db: [DataBaseCAN.Reader] <br>
<i><span style="color:green">:param</span></i> base_model: [str] 베이스로 사용할 모델의 전체 경로 또는 이름을 입력합니다. 이름만 입력 시 SVN 상 모델을 사용합니다.<br>
<i><span style="color:green">:param</span></i> *messages: 진단 모델에 포함될 대상 메시지를 입력합니다. 

```commandline
예시)

model = AscetCAN.ComDiag(DataBaseCAN.Reader(), "CanFDMCUD_HEV", "MCU_01_10ms", "MCU_02_10ms", "MCU_03_100ms")
model.generate()
```

```commandline
결과) (생성 로그)

2026-02-03 08:56:53 %{CanFDMCUD_HEV} MODEL GENERATION
2026-02-03 08:56:53 >>> DB VERSION: r21727@01
2026-02-03 08:56:53 >>> BASE MODEL: \\ ... \MessageDiag\CanFDMCUD_HEV\CanFDMCUD_HEV.zip
2026-02-03 08:56:53 >>> COPY BASE MODEL TO TEMPLATE
2026-02-03 08:56:53 >>> GENERATE HIERARCHY BY MESSAGES N=3
2026-02-03 08:56:53 >>> ... [1 / 3] MCU_01_10ms: 
2026-02-03 08:56:53 >>> ... [2 / 3] MCU_02_10ms: 
2026-02-03 08:56:53 >>> ... [3 / 3] MCU_03_100ms: 
2026-02-03 08:56:53 >>> COPY DSM LIBRARY IMPLEMENTATION
2026-02-03 08:56:54 >>> COPY CALIBRATION DATA FROM BASE MODEL
2026-02-03 08:56:54 >>> RUN EXCEPTION HANDLING
2026-02-03 08:56:54 >>> ... NO EXCEPTION FOUND
2026-02-03 08:56:55 >>> CREATED TO "C:\Users\Administrator\Downloads\CanFDMCUD_HEV" SUCCESS
```

## 3. Integration Request

통합 요청을 위한 Excel IR의 작성 편의 도구입니다.
```text
모듈 구조)

└── IntegrationRequest ------------------------------ (C) 통합요청서 작성 편의도구
    ├── ChangeHistory                               : @property, @setter 변경내역서 이름
    ├── Comment                                     : @property, @setter 비고
    ├── deliverables                                : @property, @setter 산출물 관리 경로 
    ├── parameters                                  : @property, .compare_model()의 산출물
    ├── User                                        : @property, @setter 사용자(통합요청자)
    ├── commit_all(message)                         : method; 모델 SVN commit (사용시 주의)
    ├── compare_model(prev, post, exclude_imported) : method; 모델 비교
    ├── copy_model_to_svn(src_path)                 : method; 개발 완료된 모델을 SVN 경로로 복사(Overwrite)
    ├── copy_resource(key, dst, versioning, unzip)  : method; SVN으로부터 필요 리소스를 로컬로 복사
    ├── exclude(*funcs)                             : method; 모듈 제외
    ├── resolve_model(*funcs)                       : method; 모듈 정보를 등록
    ├── resolve_svn_version(*funcs)                 : method; 모듈 SVN 정보를 등록
    ├── resolve_sdd_version()                       : method; SDD Version 등록
    ├── select_previous_svn_version(mode)           : method; 변경 대상 모델의 이전 버전 모델을 로컬로 복사
    ├── update_sdd(comment)                         : method; SDD Note 이력 자동 업데이트
    └── copy_model_to_svn(src_path)                 : method; 개발 완료된 모델을 SVN 경로로 복사(Overwrite)
```

아래의 예제 순서로 사용을 권장합니다.

```commandline
예시)

from cannect import IntegrationRequest

AUTO_COMMIT = False

# 대상 모델에 대한 객체 생성
ir = IntegrationRequest("ComDef_HEV", "ComRx_HEV", "CanFDMCUD_HEV", "CanFDMCUM_HEV", "LogIf_HEV")

# 산출물 관리 경로 지정
ir.deliverables = "사용자의 로컬 경로 지정"

# 대상 모델의 "변경 전" 모델 선택
# - mode: {'latest', 'previous', 'select'}
# - mode == "latest"  : 대상 모델 Commit 미완료 상태, 최신 revision을 "변경 전" 모델로 간주 (기본 값)
# - mode == "previous": 대상 모델 Commit 완료 상태, 직전 revision을 "변경 전" 모델로 간주
# - mode == "select"  : 대상 모델에 대한 revision을 사용자가 모두 선택(console)
ir.select_previous_svn_version(mode="latest")

# SDD 자동 업데이트 (잠재적 오류 내포)
# 사용자는 개발 내용(이력)만 입력, 그 외 버전 관리는 자동 수행
# .rtf(SDD NOTE 파일)의 형식에 따라 동작하지 않을 수 있으므로 반드시 사용자의 주의 필요
ir.update_sdd("사용자 comment")

# 모델 자동 Commit (SDD, DSM, Polyspace는 수동 Commit - 추후 개선 예정)
# SVN Commit은 되돌릴 수 없으므로 신중하게 사용
if AUTO_COMMIT:
    ir.copy_model_to_svn()
    ir.commit_all("사용자 메시지: 반드시 영문으로 작성")
    
# IR 시트 작성
ir.resolve_svn_version() # 모델, SDD, DSM, Polyspace 의 SVN 버전 기입
ir.resolve_sdd_version() # SDD Version (FunctionVersion) 기입
ir.compare_model(exclude_imported=False) # .select_previous_svn_version()이 수행된 경우 "변경 전", "변경 후" 모델 비교

print(ir)
ir.to_clipboard() # 이후 Excel IR 문서에 붙여넣기
```
```commandline
결과)

    FunctionName FunctionVersion                         SCMName SCMRev                     DSMName DSMRev ...                            SDDName SDDRev ...        Date ...               PolyspaceName PolyspaceRev
0     ComDef_HEV       00.00.008  HNB_GASOLINE\ ... \Standard...  22550                                    ...  040g00002u801q070g7g807i9bh0a.zip  53076 ...  2026-02-04 ...     BF_Result_ComDef_HEV.7z        12851
1      ComRx_HEV       00.00.008  HNB_GASOLINE\ ... \Standard...  22550                                    ...  040g00002u801q070g80h5joqq024.zip  53076 ...  2026-02-04 ...      BF_Result_ComRx_HEV.7z        12851
2  CanFDMCUD_HEV       00.05.004  HNB_GASOLINE\ ... \CANInter...  22936  canfdmcud_hev_confdata.xml  51722 ...  040g030000001og7146g3m4migjcg.zip  53637 ...  2026-02-04 ...  BF_Result_CanFDMCUD_HEV.7z        13509
3  CanFDMCUM_HEV       00.05.003  HNB_GASOLINE\ ... \CANInter...  22431                                    ...  040g030000001og714304btcfi5uo.zip  52641 ...  2026-02-04 ...  BF_Result_CanFDMCUM_HEV.7z        13203
4      LogIf_HEV       00.05.019  HNB_GASOLINE\ ... \Communic...  22500      logif_hev_confdata.xml  47210 ...  040g030000001og7143g3bkq10bua.zip  52883 ...  2026-02-04 ...      BF_Result_LogIf_HEV.7z        13203
```

## 4. ChangeHistoryManager

변경내역서 작성 편의도구입니다. IntegrationRequest의 객체를 활용하여 변경내역서의 Outline을 작성합니다.

```commandline
예시)

from cannect import ChangeHistoryManager

# ir 인스턴스가 존재한다고 가정
# ∵ ir = IntegrationRequest(*modeuls)
ppt = ChanHistoryManager(ir)

# 1페이지 작성
ppt.title       = "[CAN/공통] CAN BUS-OFF Recover Post Run 할당"   # 제목
ppt.developer   = ir.User                                         # 개발 담당
ppt.issue       = "VCDM CR10786223"                               # Issue
ppt.lcr         = "자체 개선"                                      # LCR
ppt.problem     = "OTA 업데이트 평가 중, ... 발생"                   # 문제 현상
```

```commaneline
결과) 실제 산출물은 ppt 파일로 작성되며 아래 출력은 console의 로그입니다.

2026-02-04 15:24:35 [WRITE PPT ON "D:\Archive\ ... \0000_변경내역서 양식.pptx"]
2026-02-04 15:25:05 >>> RESIZING COVER PAGE
2026-02-04 15:25:06 >>> WRITE ON "SW 기능 상세 설명 - 변경 전"
2026-02-04 15:25:06 >>> WRITE ON "SW 기능 상세 설명 - 변경 후"
2026-02-04 15:25:06 >>> GENERATE SLIDES 
2026-02-04 15:25:07 >>> WRITING PREVIOUS MODEL DETAILS...
2026-02-04 15:25:07 >>> ... CAND @18550
2026-02-04 15:25:07 >>> WRITING REVISED MODEL DETAILS...
2026-02-04 15:25:07 >>> ... CAND @23018
```


## 5. ASCET MODULE(AMD)
### 5.1. Ascet.Amd

4종 .amd (.main, .data, .implementation, .specification)에 대한 Ascet.AmdIO의 Wrapper 클래스입니다.

```commandline
from cannect import Ascet

# READ *.amd
# INSTANCE {amd} CONTAINS FOLLOWING ATTRIBUTES
# .name:           [str] NAME OF MODULE
# .main: [<Ascet.AmdIO>] Ascet.AmdIO({*.main.amd}) 
# .impl: [<Ascet.AmdIO>] Ascet.AmdIO({*.implementation.amd}) 
# .data: [<Ascet.AmdIO>] Ascet.AmdIO({*.data.amd}) 
# .spec: [<Ascet.AmdIO>] Ascet.AmdIO({*.specification.amd}) 

src = # {*.main.amd} 또는 {*.zip} (모델 전체 경로)
amd = Ascet.Amd(src)
```

### 5.2. Ascet.AmdIO
개별 *.amd 파일에 대한 IO 클래스입니다.

#### 5.2.1. <i>.root</i>
```commandline
main = amd.main
print(main.root)
```
```commandline
결과
name                                                         ComDef_HEV
nameSpace             /HNB_GASOLINE/_29_CommunicationVehicle/Standar...
OID                                      _040g00002u801q070g7g807i9bh0a
timeStamp                                           2025-10-01T06:48:17
componentType                                              ASCET_Module
specificationType                                                 CCode
defaultProjectName                                   ComDef_HEV_DEFAULT
defaultProjectOID                        _040g1j9410g01q87180hrfqf5892o
path                  D:\ETASData\ASCET6.1\Export\ComDef_HEV\ComDef_...
file                                                ComDef_HEV.main.amd
model                                                        ComDef_HEV
type                                                      ComponentMain
dtype: object
```
#### 5.2.2. <i>.digestValue</i> & <i>.signatureValue</i>
```commandline
print(main.digestValue)
print("---")
print(main.signatureValue)
```
```commandline
결과
P4vSzV9B/VN5kcuO0ICAfxWO2vo=
---
bB8aNE2ULCnQ+BB5y5HVHnwsnRZUzbCX1cqPHZ2hik1e3CZ4aMXmeZezMZl2nrXd
dieNjpiHg2iTOdQurIad4mLu0ixv2UVLa7FC0SgkBarFV7VgAYAXq8x7xd/KrEaA
EAeJmWb+uKW5hkQwrQ7bHe3BuNOoPmX1uIFZv7aKqmZDVdypC+0C3q1CbbeMjfWU
xwMQ8jsUjXlJCjdtpyBhPlS8O/dJ5tm7mnNTrSk8wp+nSbk17E5g9xy9SmyC3CUZ
0I7XDtbazFkOQKSkBgwpmEv0qkdeeQJ/JuSePXFi66E962zf+CqQ4PTZX2e9lW1u
k8jWuLYv6t5ckBo/Tn6hoQ==
```
#### 5.2.3. <i>.dataframe(tag:str, depth:str)</i>
tag의 Attribute를 데이터프레임으로 변환합니다.<br>
<i style="color:green;">@param</i> tag: [str] 변환하고자 하는 태그 이름 e.g. "Element", "MethodSignature"<br>
<i style="color:green;">@param</i> depth: [str] 선택한 태그 하위 태그 적용 깊이 e.g. "recursive"

```commandline
print(main.dataframe('Element', depth='recursive'))
print('---')
print(main.dataframe('MethodSignature', depth='tag'))
```
```commandline
결과
                            name                             OID ignore                                            comment modelType basicModelType unit      kind     scope virtual dependent volatile calibrated    set    get  read write reference maxSizeX                                      componentName                     componentID       model
0                ABS_ActvSta_Can  _040g1ngg00p91o07186g9qpv1tv0a  false       ABS_ActiveStatus ##2G##ESC - TCS11 - ABS_ACT    scalar          udisc        message  exported   false     false     true       true  false  false  true  true     false      NaN                                                NaN                             NaN  ComDef_HEV
1               ABS_DfctvSta_Can  _040g1ngg01a01no71c8g7rr1uh8ga  false    ABS_DefectiveStatus ##2G##ESC - TCS11 - ABS_DEF    scalar          udisc        message  exported   false     false     true       true  false  false  true  true     false      NaN                                                NaN                             NaN  ComDef_HEV
2                ABS_DiagSta_Can  _040g1ngg00p91o07182g9bnv64o0e  false  ABS_DiagnosticStatus ##2G##ESC - TCS11 - ABS_DIAG    scalar          udisc        message  exported   false     false     true       true  false  false  true  true     false      NaN                                                NaN                             NaN  ComDef_HEV
...                          ...                             ...    ...                                                ...       ...            ...  ...       ...       ...     ...       ...      ...        ...    ...    ...   ...   ...       ...      ...                                                ...                             ...         ...
1172       xEV_TotGridEnergy_Can  _040g1ngg01a01og70g8g5pjg6r3lc  false                 Total grid energy into the battery    scalar           cont        message  exported   false     false     true       true  false  false  true  true     false      NaN                                                NaN                             NaN  ComDef_HEV
1173         CRC16bit_Calculator  _040g1ngg00p91og70gbg6kpeec400  false                      CRC 16bit Calculator Instance   complex          class            NaN     local     NaN       NaN      NaN        NaN  false  false  true  true     false      NaN  /HNB_GASOLINE/_29_CommunicationVehicle/CANInte...  _040g1ngg01pp1oo708a0du6locrr2  ComDef_HEV
1174          CRC8bit_Calculator  _040g1ngg01a01o8704fg42b3o0102  false                       CRC 8bit Calculator Instance   complex          class            NaN     local     NaN       NaN      NaN        NaN  false  false  true  true     false      NaN  /HNB_GASOLINE/_29_CommunicationVehicle/CANInte...  _040g1ngg01pp1oo708cg4rviuqor2  ComDef_HEV

[1175 rows x 22 columns]
---
                     name                             OID public default defaultMethod hidden availableForOS       model
0        _ABS_ESC_01_10ms  _040g1ngg00p91o870kb0a7d8r4524   true   false          true  false           true  ComDef_HEV
1            _ACU_02_00ms  _040g030000001mo7109g4avsmjn5i   true   false         false  false           true  ComDef_HEV
2           _BCM_12_200ms  _040g030000001mo710eg5p0lpf73a   true   false         false  false           true  ComDef_HEV
..                    ...                             ...    ...     ...           ...    ...            ...         ...
62          _SMK_02_200ms  _040g1j9410g01q071g90p9vm1m4g2   true   false         false  false           true  ComDef_HEV
63          _TMU_01_200ms  _040g1ngg00p91o871cbg8vcrhmigk   true   false         false  false           true  ComDef_HEV
64        _WAKEUP_01_00ms  _040g030000001mo7109g4a84q0t5g   true   false         false  false           true  ComDef_HEV

[65 rows x 8 columns]
```
#### 5.2.4. <i>.datadict(tag:str, depth:str)</i>
1.2.3.절의 dictionary 형태 (예제 없음)

#### 5.2.5. <i>.export(path:str)</i>
파일로 저장
```commandline
main.export(r'./')
```

#### 5.2.6. 기타 기능
```commandline
# .export_to_downloads()
# 1.2.5.절의 저장 경로를 C:\User\Downloads 로 지정
```

```commandline
# .findParent(*elems:Element)
# Element의 부모 Element 를 리턴
```

```commandline
# .serialize()
# export를 위한 문자열을 리턴
```

```commandline
# .strictFind(tag:str, **kwargs)
# 태그와 Attribute가 kwargs의 조건을 만족하는 태그를 리턴
```

```commandline
# .replace(tag:str, attr_name:str, attr_value:dict)
# @tag와 @attr_name에 부합하는 태그를 찾은 뒤 attr_value.key값을 attr_value.value로 변경
```

### 5.3. WorkspaceIO
워크스페이스 또는 SVN 전체 프로젝트 접근
