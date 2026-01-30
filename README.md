# cannect

<b>HMG/EMS ASW CONVENIENCE TOOL</b><br>
THIS FRAMEWORK IS PURPOSE-BUILT AND WILL NOT FUNCTION IN ENVIRONMENTS WHERE THE DOMAIN IS NOT VERIFIED OR AUTHORIZED. ALL RESOURCES REFER TO THE COMPANY'S INTERNAL NETWORK(INTRANET), AND THIS FRAMEWORK PROVIDES CONVENIENCE TOOLS FOR THOSE RESOURCES. THE RESOURCES THEMSELVES ARE PROCESSED TO PREVENT REMOVAL FROM THE INTRANET, AND USERS MUST EXERCISE CAUTION. ANY ATTEMPT TO EXPORT INTERNAL RESOURCES USING THIS FRAMEWORK MAY RESULT IN DISADVANTAGES OR DISCIPLINARY ACTION IN ACCORDANCE WITH THE COMPANY'S SECURITY POLICY.<br><br>
<b>HMG/EMS ASW 편의 도구</b><br>
이 프레임워크는 특수한 목적을 위해 제작되었으며 사용하는 도메인이 검증 또는 허용되지 않은 환경에서는 작동이 불가합니다. 모든 리소스는 회사 내부망을 참조하며 본 프레임워크는 그 리소스에 대한 편의 도구를 제공합니다. 리소스 자체는 회사 내부망에서 반출되지 않도록 처리되며 사용자 또한 유의하여 사용하여야 합니다. 만일 이 프레임워크를 사용하여 내부 리소스를 반출하려는 시도를 할 경우 사내 보안 정책에 의거 불이익 또는 처벌을 받을 수 있습니다

## USER GUIDE
### INITIALIZE

리소스 사용을 위한 내부 서버 mount 필요하다. (매 실행 시 상위에 삽입되어야 하는 코드)
```commandline
from cannect import mount

mount(r"D:\SVN") # 사용자 Local의 SVN 최상위 경로를 입력
# 또는
mount()          # 미입력 시, 내부 서버에 있는 SVN 경로를 사용(성능 저하 모드 및 사용자간 충돌 가능성 내포)
```

### 1. ASCET MODULE(AMD)
#### 1.1. Ascet.Amd
▲*.main.amd ▲*.data.amd ▲*.implementation.amd ▲*.specification.amd 에 대한 Ascet.AmdIO의 Wrapper 클래스이다.

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

#### 1.2. Ascet.AmdIO
개별 *.amd 파일에 대한 IO 클래스이다.

##### 1.2.1. <i>.root</i>
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
##### 1.2.2. <i>.digestValue</i> & <i>.signatureValue</i>
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
##### 1.2.3. <i>.dataframe(tag:str, depth:str)</i>
tag의 Attribute를 데이터프레임으로 변환한다.<br>
@param tag: [str] 변환하고자 하는 태그 이름 e.g. "Element", "MethodSignature"<br>
@param depth: [str] 선택한 태그 하위 태그 적용 깊이 e.g. "recursive"

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
##### 1.2.4. <i>.datadict(tag:str, depth:str)</i>
1.2.3.절의 dictionary 형태 (예제 없음)

##### 1.2.5. <i>.export(path:str)</i>
파일로 저장
```commandline
main.export(r'./')
```

##### 1.2.6. 기타 기능
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

#### 1.3. WorkspaceIO
워크스페이스 또는 SVN 전체 프로젝트 접근

### 2. CAN
#### 2.1. Database
```commandline
from cannect import DataBaseCAN

db = DataBaseCAN.Reader(src='')
# 특정 프로젝트를 위한 DB를 사용할 경우 json 파일 형식의 데이터를 @src에 사용
# 미적용 시 SVN 내 최신 DB 사용
print(db)
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
```

2.1.1. Database/Reader - 속성
```commandline
print(db.source) # json 파일 전체 경로 / pd.DataFrame 입력 시 "direct"
print(db.traceability) # 원본 DB 이름 (Excel 파일명)
print(db.revision) # 원본 DB의 SVN Revision 및 로컬 재생성 횟수
```
```commandline
결과
E:\SVN\dev.bsw\ ...{보안상 생략}... \dev\자체제어기_KEFICO-EMS_CANFD_r21713@03.json
자체제어기_KEFICO-EMS_CANFD
r21713@03
```