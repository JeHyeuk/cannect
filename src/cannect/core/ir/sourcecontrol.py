from cannect.config import env
from cannect.core.subversion import SubVersion
from cannect.schema import DataDictionary
from cannect.utils import tools

from datetime import datetime
from lxml import etree
from pandas import DataFrame
from pathlib import Path
from typing import Union
import os, re, zipfile, py7zr


SVN = SubVersion(env.SVN_PATH)
class SourceControl:

    @classmethod
    def update(cls):
        return (f'{SVN.MODEL.update()}\n'
                f'{SVN.CONF.update()}\n'
                f'{SVN.IR.update()}\n'
                f'{SVN.HISTORY.update()}\n'
                f'{SVN.UNECE.update()}')

    @classmethod
    def get_items(cls, path:Union[Path, str]) -> DataFrame:
        r"""
        입력된 경로 상 통합요청 산출물을 전체 수집한다.
        수집 항목:
            - *.amd 파일 계열 (*.dp.amd는 자동 제외)
            - *.rtf 파일 계열
            - *.xml 파일
            - *.7z 파일
        :param path:
        :return: [출력 예시]
                                           name            date            path   type                                    svn                          model
                  0000_EMS_IsgWarning ... .pptx  20260701165303  D:\Archive\...    ppt         E:\SVN\GSL_Release\4_SW변경이력                            NaN
        0000_HNB_SW_IR_EMS_IsgWarning ... .xlsm  20260722080058  D:\Archive\...     ir  E:\SVN\GSL_Build\8_IntegrationRequest                            NaN
                           CanFDEMSM14.data.amd  20230628105825  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                 CanFDEMSM14.implementation.amd  20230628105825  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                           CanFDEMSM14.main.amd  20230628105825  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                        CanFDEMSM14.scmdata.amd  20230628105825  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                  CanFDEMSM14.specification.amd  20230628105825  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                           CanFDEMSM14.data.amd  20260722100044  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                 CanFDEMSM14.implementation.amd  20260722100044  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                           CanFDEMSM14.main.amd  20260722100044  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                        CanFDEMSM14.scmdata.amd  20260722100044  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                  CanFDEMSM14.specification.amd  20260722100044  D:\Archive\...  model                                    NaN                    CanFDEMSM14
                         FunctionDefinition.rtf  20230628085921  D:\Archive\...    sdd               E:\SVN\GSL_Build\7_Notes  040g1ngg02431oo71gf14re1v3jdq
                         FunctionDefinition.rtf  20260722095949  D:\Archive\...    sdd               E:\SVN\GSL_Build\7_Notes  040g1ngg02431oo71gf14re1v3jdq
        """
        path = Path(path)

        items = []
        for root, dirs, files in os.walk(path):
            for filename in files:
                file = Path(root) / filename
                prop = {
                    'name': filename,
                    'date': int(datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y%m%d%H%M%S")),
                    'path': file,
                }
                if filename.endswith('_confdata.xml'):
                    prop.update({
                        'type': 'conf',
                        'model': filename.split('_confdata')[0],
                        'svn': SVN.CONF
                    })
                elif filename.endswith('.rtf'):
                    prop.update({
                        'type': 'sdd',
                        'model': file.parent.name,
                        'svn': SVN.SDD
                    })
                elif filename.endswith('.7z') and filename.startswith('BF_Result_'):
                    prop.update({
                        'type': 'ps',
                        'model': filename.split(".")[0].replace("BF_Result_", ""),
                        'svn': SVN.UNECE
                    })
                elif filename.endswith('.amd') and (not filename.endswith('.dp.amd')):
                    prop.update({
                        'type': 'model',
                        'model': filename.split(".")[0],
                    })
                elif filename.split('_')[0].isdigit():
                    if filename.endswith('.xlsm'):
                        prop.update({
                            'type': 'ir',
                            'svn': SVN.IR
                        })
                    if filename.endswith('.pptx'):
                        prop.update({
                            'type': 'ppt',
                            'svn': SVN.HISTORY
                        })
                else:
                    continue
                items.append(prop)
        return DataFrame(items)


    __slots__ = [
        'dst',
        'src',
        'svn',
    ]

    def __init__(self, path: Union[Path, str]):
        dst = DataDictionary(root=Path(path))
        src = DataDictionary()
        dst.root.mkdir(parents=True, exist_ok=True)
        uid = dst.root.name

        for item in ['conf', 'model', 'ps', 'sdd']:
            dst[item] = DataDictionary(
                prev=dst.root / f'{item}/변경 전',
                post=dst.root / f'{item}/변경 후',
            )
            for path in dst[item].values():
                path.mkdir(parents=True, exist_ok=True)

        for file in os.listdir(dst.root):
            try:
                if file.split("_")[0].isdigit():
                    if file.endswith('.xlsm'):
                        src.ir = {
                            'src': dst.root / file,
                            'dst': SVN.IR,
                            'date': None
                        }
                    if file.endswith('.pptx'):
                        src.ppt = {
                            'src': dst.root / file,
                            'dst': SVN.HISTORY,
                            'date': None
                        }
                    continue
            except (IndexError, ValueError, Exception):
                continue

        if not 'ppt' in src:
            src.ppt = {
                'src': tools.copy_to(env.SERVER_TEMP.parent / 'src/0000_변경내역서 양식.pptx', dst.root),
                'dst': SVN.HISTORY,
                'date': None
            }
            src.ppt.src = src.ppt.src.rename(src.ppt.src.with_name(f'0000_변경내역_{uid.replace(" ", "_")}.pptx'))
        if not 'ir' in src:
            src.ir = {
                'src': tools.copy_to(SVN.IR / '0000_HNB_SW_IR_.xlsm', dst.root),
                'dst': SVN.IR,
                'date': None,
            }
            src.ir.src = src.ir.src.rename(src.ir.src.with_name(f'0000_HNB_SW_IR_{uid.replace(" ", "_")}.xlsm'))

        self.dst = dst
        self.src = src
        self.svn = DataDictionary()
        return

    def __str__(self) -> str:
        """
        입력된 경로를 순회(os.walk(path) 또는 그에 준하는 순회 방법)하며 파일리스트를 모두 찾고
        사용자가 print 또는 display 가능한 형태의 문자열로 리턴
        예시)
        root
         ㄴ schema
               ㄴ 고객 요청
                    ㄴ template.xlsx
               ㄴ 자체 개선
                    ㄴ labels.txt
         ㄴ 발주서.xlsx
        """
        path = self.dst.root
        lines = []
        indent = " ㄴ "
        prefix = "   "  # indent와 동일한 너비의 공백 (정렬용)

        def build_tree(current_path: Path, depth: int):
            # 현재 경로의 항목들을 정렬 (디렉토리 먼저, 그 다음 파일)
            try:
                entries = sorted(current_path.iterdir(), key=lambda e: (e.is_file(), e.name))
            except PermissionError:
                return

            for entry in entries:
                lines.append(f"{prefix * depth}{indent}{entry.name}")
                if entry.is_dir():
                    build_tree(entry, depth + 1)

        # 루트 경로 이름 추가
        lines.append(path.name)
        build_tree(path, 0)
        return "\n".join(lines)

    def get_items_by_ir(self, ir_sheet:DataFrame) -> DataFrame:
        items = [{
            'name': self.src.ir.src.name,
            'type': 'ir',
            'date': int(datetime.fromtimestamp(self.src.ir.src.stat().st_mtime).strftime("%Y%m%d%H%M%S")),
            'path': self.src.ir.src,
            'svn': self.src.ir.dst
        }, {
            'name': self.src.ppt.src.name,
            'type': 'ppt',
            'date': int(datetime.fromtimestamp(self.src.ppt.src.stat().st_mtime).strftime("%Y%m%d%H%M%S")),
            'path': self.src.ppt.src,
            'svn': self.src.ppt.dst
        }]
        for md in ir_sheet.index:
            svn = self.svn[md]
            dst = self.dst.model.post / md
            dst.mkdir(parents=True, exist_ok=True)
            tools.clear(dst, leave_path=True)
            for filename in [
                f'{md}.main.amd',
                f'{md}.data.amd',
                f'{md}.implementation.amd',
                f'{md}.scmdata.amd',
                f'{md}.specification.amd',
                f'{md.lower()}_confdata.xml',
                ir_sheet.loc[md, "SDDName"].split('.')[0],
                f'BF_Result_{md}.7z'
            ]:

                try:
                    found = tools.find_file(self.dst.root, filename)
                    if not isinstance(found, list):
                        found = [found]
                except FileNotFoundError:
                    continue

                for file in found:
                    type = filename.split('.')[-1] if '.' in filename else 'sdd'
                    if type == '7z':
                        svn = SVN.UNECE
                    elif type == 'xml':
                        svn = SVN.CONF
                    else:
                        svn = None
                    items.append({
                        'name': filename,
                        'type': filename.split('.')[-1] if '.' in filename else 'sdd-temp',
                        'model': filename.split('.')[0] if filename.endswith('.amd') else None,
                        'date': int(datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y%m%d%H%M%S")),
                        'path': file,
                        'svn': svn
                    })
        return DataFrame(items) \
            .sort_values(by=['date'], ascending=False, ignore_index=True)

    def pack(self, ir_sheet:DataFrame) -> DataFrame:
        r"""
        통합요청서(FTN List) 기반 SVN Commit 대상 산출물을 List-Up하여 데이터프레임
        형태로 리턴한다.

        선행 method self.get_item()으로 수집한 root 경로 내 모든 산출물에 대해
        중복 항목은 시간 순으로 나열하여 오래된 항목을 버리고 최신 항목만 남긴다. 또한
        압축 필요 항목(*.rtf 세트, *.amd 세트)은 자동 압축하여 SVN 형상 관리 형식을
        준수한다.

        :param ir_sheet: [DataFrame]
        :return: [example]
                                           name   type          path                                                svn
        0000_HNB_SW_IR_EMS_IsgWarning ... .xlsm     ir  \\kefico\...              E:\SVN\GSL_Build\8_IntegrationRequest
                  0000_EMS_IsgWarning ... .pptx    ppt  \\kefico\...                     E:\SVN\GSL_Release\4_SW변경이력
                       BF_Result_CanFDEMSM14.7z     7z  \\kefico\...  E:\SVN\Autron_CoWork\사이버보안\Module_Test_Results
                                CanFDEMSM14.zip  model  \\kefico\...  E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_Comm...
              040g1ngg02431oo71gf14re1v3jdq.zip    sdd  \\kefico\...                           E:\SVN\GSL_Build\7_Notes
        """
        items = self.get_items_by_ir(ir_sheet) \
                .drop_duplicates(subset=['name'], keep='first', ignore_index=True)
        if 'model' in items.columns:
            for md, source in items[items['type'] == 'amd'].groupby('model'):
                dst = self.dst.model.post / md
                for src in source['path']:
                    tools.copy_to(Path(src), dst)
                if not f'{md}.scmdata.amd' in os.listdir(dst):
                    # TODO
                    print(f'#TODO missing "{md}.scmdata.amd" <- check before commit')
                file = tools.zip(dst, self.dst.model.post, overwrite=True)
                items.loc[len(items)] = {
                    'name': file.name,
                    'path': file,
                    'svn': self.svn[md].model.src,
                    'type': 'model',
                }
                tools.clear(dst, leave_path=False)

        for sdd in items[items['type'] == 'sdd-temp']['path']:
            file = tools.zip(sdd, self.dst.sdd.post, overwrite=True)
            items.loc[len(items)] = {
                'name': f'{sdd.name}.zip',
                'path': file,
                'svn': SVN.SDD,
                'type': 'sdd'
            }
        items = items[~items['type'].isin(['amd', 'sdd-temp'])] \
                .drop(columns=[c for c in ['model', 'date'] if c in items.columns]) \
                .sort_index(ignore_index=True)
        return items


# SVN commit 전 개발자 산출물과 SVN 소스 비교 목적 함수
# written by Claud sonnect 4.6


# ──────────────────────────────────────────────
# 1. XML 비교
# ──────────────────────────────────────────────
def _normalize_xml(path: Path) -> etree._Element:
    """XML을 파싱하고 정규화(속성 정렬, 공백 제거)하여 Element 반환."""
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=False)
    tree = etree.parse(str(path), parser)
    root = tree.getroot()
    _sort_attributes(root)
    return root


def _sort_attributes(element: etree._Element):
    """재귀적으로 모든 요소의 속성을 키 기준 정렬 (원시 데이터 소스 단위 비교)."""
    attrib = dict(sorted(element.attrib.items()))
    element.attrib.clear()
    element.attrib.update(attrib)
    for child in element:
        _sort_attributes(child)


def _elements_equal(e1: etree._Element, e2: etree._Element) -> bool:
    """두 XML Element를 재귀적으로 비교."""
    if e1.tag != e2.tag:
        return False
    if (e1.text or "").strip() != (e2.text or "").strip():
        return False
    if (e1.tail or "").strip() != (e2.tail or "").strip():
        return False
    if dict(e1.attrib) != dict(e2.attrib):
        return False
    if len(e1) != len(e2):
        return False
    return all(_elements_equal(c1, c2) for c1, c2 in zip(e1, e2))


def _compare_xml(src1: Path, src2: Path) -> bool:
    """XML 파일 원시 데이터 소스 단위 비교."""
    try:
        root1 = _normalize_xml(src1)
        root2 = _normalize_xml(src2)
        return _elements_equal(root1, root2)
    except etree.XMLSyntaxError:
        return False


# ──────────────────────────────────────────────
# 2. ZIP (XML 묶음) 비교
# ──────────────────────────────────────────────
def _read_zip_xml_contents(zf: zipfile.ZipFile) -> dict[str, etree._Element]:
    """ZIP 내 .xml 파일을 이름→정규화 Element 딕셔너리로 반환."""
    result = {}
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=False)
    for info in zf.infolist():
        if (info.filename.endswith(".xml") or info.filename.endswith(".amd")) and not info.is_dir():
            with zf.open(info) as f:
                root = etree.parse(f, parser).getroot()
                _sort_attributes(root)
                result[info.filename] = root
    return result


def _compare_zip_xml(src1: Path, src2: Path) -> bool:
    """ZIP(XML 묶음) 내용물 비교."""
    with zipfile.ZipFile(src1, "r") as zf1, zipfile.ZipFile(src2, "r") as zf2:
        contents1 = _read_zip_xml_contents(zf1)
        contents2 = _read_zip_xml_contents(zf2)

        if set(contents1.keys()) != set(contents2.keys()):
            return False

        return all(
            _elements_equal(contents1[name], contents2[name])
            for name in contents1
        )


# ──────────────────────────────────────────────
# 3. ZIP (Nested RTF 묶음) 비교
# ──────────────────────────────────────────────
_RTF_STRIP_RE = re.compile(
    r"\\[a-z]+\d*\s?|[{}]|\\\n|\\\r",
    re.IGNORECASE,
)


def _normalize_rtf(raw: bytes) -> str:
    """RTF 바이트에서 제어어·구조 문자를 제거한 평문 반환."""
    text = raw.decode("latin-1", errors="replace")
    text = _RTF_STRIP_RE.sub("", text)
    return " ".join(text.split())  # 연속 공백 통일


def _read_zip_rtf_contents(zf: zipfile.ZipFile) -> dict[str, str]:
    """ZIP 내 .rtf 파일을 이름→정규화 평문 딕셔너리로 반환."""
    result = {}
    for info in zf.infolist():
        if info.filename.lower().endswith(".rtf") and not info.is_dir():
            with zf.open(info) as f:
                result[info.filename] = _normalize_rtf(f.read())
    return result


def _compare_zip_rtf(src1: Path, src2: Path) -> bool:
    """ZIP(Nested RTF 묶음) 내용물 비교."""
    with zipfile.ZipFile(src1, "r") as zf1, zipfile.ZipFile(src2, "r") as zf2:
        contents1 = _read_zip_rtf_contents(zf1)
        contents2 = _read_zip_rtf_contents(zf2)

        if set(contents1.keys()) != set(contents2.keys()):
            return False

        return all(
            contents1[name] == contents2[name]
            for name in contents1
        )


def _detect_zip_subtype(src: Path) -> str:
    """
    ZIP 파일 내부를 최소 탐색하여 서브타입 결정.
      - 'xml' : .xml 파일이 존재
      - 'rtf' : .rtf 파일이 존재 (nested 포함)
      - 'unknown'
    """
    with zipfile.ZipFile(src, "r") as zf:
        for info in zf.infolist():
            name_lower = info.filename.lower()
            if name_lower.endswith(".xml") or name_lower.endswith('.amd'):
                return "xml"
            if name_lower.endswith(".rtf"):
                return "rtf"
    return "unknown"


# ──────────────────────────────────────────────
# 4. 7Z (Polyspace .log 비교)
# ──────────────────────────────────────────────
_PS_IGNORE_RE = re.compile(
    r"^\s*(?:"
    r"Date\s*:|"
    r"Time\s*:|"
    r"Elapsed\s*time|"
    r"Analysis\s*started|"
    r"Analysis\s*ended|"
    r"Host\s*:|"
    r"Version\s*:"
    r")",
    re.IGNORECASE,
)


def _normalize_log_lines(raw: bytes) -> list[str]:
    """
    .log 바이트를 줄 단위로 읽어 정규화된 줄 목록 반환.
    - 타임스탬프·호스트 등 환경 의존 줄 제거
    - 선행/후행 공백 제거, 빈 줄 제거
    """
    lines = []
    for raw_line in raw.splitlines():
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        if _PS_IGNORE_RE.match(line):
            continue
        lines.append(line)
    return lines


def _read_7z_log_contents(path: Path) -> dict[str, list[str]]:
    """7z 아카이브 내 .log 파일을 이름→정규화 줄 목록 딕셔너리로 반환."""
    result = {}
    with py7zr.SevenZipFile(str(path), mode="r") as archive:
        all_files = archive.getnames()
        log_files = [f for f in all_files if f.lower().endswith(".log")]

        if not log_files:
            return result

        extracted = archive.read(targets=log_files)  # {name: BytesIO}
        for name, bio in extracted.items():
            result[name] = _normalize_log_lines(bio.read())
    return result


def _compare_7z_log(src1: Path, src2: Path) -> bool:
    """7z 내 .log 파일만 추출하여 내용 비교."""
    contents1 = _read_7z_log_contents(src1)
    contents2 = _read_7z_log_contents(src2)

    if set(contents1.keys()) != set(contents2.keys()):
        return False

    return all(
        contents1[name] == contents2[name]
        for name in contents1
    )


# ══════════════════════════════════════════════
# MASTER FUNCTION
# ══════════════════════════════════════════════
def is_same(src1: Path, src2: Path) -> bool:
    """
    두 파일이 논리적으로 동일한지 비교하는 마스터 함수.

    지원 형식:
      .xml        → XML 원시 데이터 소스 단위 비교
      .zip (XML)  → 내부 .xml 파일 내용 비교
      .zip (RTF)  → 내부 .rtf 파일 정규화 텍스트 비교
      .7z         → 내부 .log 파일만 추출하여 비교

    Parameters
    ----------
    src1, src2 : Path
        비교할 두 파일의 경로

    Returns
    -------
    bool
        두 파일이 동일하면 True, 다르면 False
    """
    src1, src2 = Path(src1), Path(src2)

    if not src1.exists() or not src2.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {src1}, {src2}")

    suffix = src1.suffix.lower()

    if suffix == ".xml":
        return _compare_xml(src1, src2)

    if suffix == ".zip":
        subtype = _detect_zip_subtype(src1)
        if subtype == "xml":
            return _compare_zip_xml(src1, src2)
        elif subtype == "rtf":
            return _compare_zip_rtf(src1, src2)
        else:
            raise ValueError(f"지원하지 않는 ZIP 서브타입: {src1}")

    if suffix == ".7z":
        return _compare_7z_log(src1, src2)

    raise ValueError(f"지원하지 않는 파일 형식: {suffix}")


if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)

    # print(is_same(
    #     src1=r'E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\LIN\Diagnosis\LinD\LinD-22986.zip',
    #     src2=r'E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\LIN\Diagnosis\LinD\LinD-22767.zip'
    # ))


    sc = SourceControl(r'\\kefico\keti\ENT\SDT\EMS_Tool\cannect\cloud\22011148\ir\EMS_IsgWarning 신호 조건 중 자동변속기에 CVT 추가')
    # print(sc.get_items(sc.dst.root))
    # print(sc)