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


class Compare:

    @classmethod
    def raw(cls, src1:Path, src2:Path):
        return src1.read_bytes() == src2.read_bytes()

    @classmethod
    def raw_text(cls, src1:Path, src2:Path, encoding:str='utf-8'):
        return src1.read_text(encoding=encoding) == src2.read_text(encoding=encoding)

    @classmethod
    def detect_zip_subtype(cls, src: Path) -> str:
        """
        ZIP 파일 내부를 최소 탐색하여 서브타입 결정.
          - 'xml' : .xml 파일이 존재
          - 'rtf' : .rtf 파일이 존재 (nested 포함)
          - 'unknown'
        """
        with zipfile.ZipFile(src, "r") as zf:
            for info in zf.infolist():
                name_lower = info.filename.lower()
                if name_lower.endswith('.amd'):
                    return "amd"
                if name_lower.endswith(".rtf"):
                    return "rtf"
        raise TypeError(f'"{src}" is not a valid file to compare')

    @classmethod
    def read_file_from_archive(cls, archive_path: str | Path, target_ext: str) -> bytes:
        """
        압축 파일(.zip / .7z) 안에서 특정 확장자 파일 하나를 찾아 bytes로 반환.

        Args:
            archive_path : 압축 파일 경로
            target_ext   : 찾을 확장자 (예: ".csv", ".json", ".txt")

        Returns:
            해당 파일의 bytes 데이터

        Raises:
            FileNotFoundError : 해당 확장자 파일이 없을 때
            ImportError       : .7z인데 py7zr 미설치 시
        """
        archive_path = Path(archive_path)
        target_ext = target_ext.lower()
        suffix = archive_path.suffix.lower()

        # ── .zip ────────────────────────────────────────────────
        if suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                matched = [
                    name for name in zf.namelist()
                    if Path(name).name.endswith(target_ext)
                ]
                if not matched:
                    raise FileNotFoundError(
                        f"[ZIP] '{target_ext}' 파일을 찾을 수 없습니다."
                    )
                # 첫 번째 매칭 파일을 메모리에서 읽기
                return zf.read(matched[0])

        # ── .7z ─────────────────────────────────────────────────
        elif suffix == ".7z":
            with py7zr.SevenZipFile(archive_path, mode="r") as sz:
                all_names = sz.getnames()
                matched = [
                    name for name in all_names
                    if Path(name).name.endswith(target_ext)
                ]
                if not matched:
                    raise FileNotFoundError(
                        f"[7Z] '{target_ext}' 파일을 찾을 수 없습니다."
                    )
                # 특정 파일만 선택적으로 읽기
                extracted = sz.read([matched[0]])
                bio = extracted[matched[0]]
                return bio.read()

        else:
            raise ValueError(f"지원하지 않는 형식입니다: {suffix}")


    def __init__(self, src1: Path, src2: Path):
        self.src1, self.src2 = src1, src2 = Path(src1), Path(src2)

        __same__ = False
        if not src1.exists() or not src2.exists():
            raise FileNotFoundError(src1, src2)

        if src1.suffix.lower() == '.xml':
            __same__ = self.raw(src1, src2)
        elif src1.suffix.lower() == '.zip':
            subtype = self.detect_zip_subtype(src1)
            if subtype == 'amd':
                byte1 = self.read_file_from_archive(src1, '.main.amd')
                byte2 = self.read_file_from_archive(src2, '.main.amd')
            elif subtype == 'rtf':
                byte1 = self.read_file_from_archive(src1, 'FunctionDefinition.rtf')
                byte2 = self.read_file_from_archive(src2, 'FunctionDefinition.rtf')
            else:
                raise TypeError()
            __same__ = byte1 == byte2
        elif src1.suffix.lower() == '.7z':
            byte1 = self.read_file_from_archive(src1, '.log')
            byte2 = self.read_file_from_archive(src2, '.log')
            __same__ = byte1 == byte2
        else:
            raise TypeError(f'"{src1}" is not a valid file to compare')

        self.__same__ = __same__
        return

    def __bool__(self):
        return self.__same__

    def __str__(self):
        return str(self.__same__)




if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)


    compare = Compare(
        r'E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\LIN\Diagnosis\LinD\LinD-22767.zip',
        r'E:\SVN\model\ascet\trunk\HNB_GASOLINE\_29_CommunicationVehicle\LIN\Diagnosis\LinD\LinD-22986.zip'
    )
    print(compare)
