from cannect.config import env
from cannect.utils import tools
from pathlib import Path
from datetime import datetime
import os


class Deliverables:

    # Resources = { U | Formula, Conf-Data, BSW-Auxiliary, SDD-Note, OS-Task-Info }
    __slots__ = (
        "Root",
        "Requirement", "BuildEnv", "Workspace", "Model",
        "Resources", "CGen", "ROM", "Test", "Others"
    )

    def __init__(self, base_path: str=''):
        """
        IR 산출물 관리 폴더 생성,
        @base_path 경로 입력 시 하위에 @sub_path 이름으로 폴더 생성
        @base_path 미 입력 시, "다운로드"폴더 하위에 "{생성 날짜}_IR_산출물" 이름으로 자동 폴더
        생성 후 @sub_paths 이름의 하위 폴더 생성
        @sub_paths 하위 폴더 리스트 미 지정 시 디폴트 값 자동 할당

        @base_path : [str] 산출물 관리 경로
        """
        if base_path:
            self.Root = Path(base_path)
        else:
            self.Root = Path(env.DOWNLOADS / f'{datetime.now().strftime("%Y%m%d")}_IR_산출물')
        root = self.Root

        os.makedirs(root, exist_ok=True)
        for n, path in enumerate(self.__slots__, start=0):
            if path == "Root":
                continue
            full_path = Path(os.path.join(root, f'{str(n).zfill(2)}_{path}'))
            setattr(self, path, full_path)

            os.makedirs(full_path, exist_ok=True)
            if path == "Model":
                os.makedirs(os.path.join(full_path, f'Prev'), exist_ok=True)
                os.makedirs(os.path.join(full_path, f'Post'), exist_ok=True)

        if not any(file.endswith('.xlsm') for file in os.listdir(root)):
            try:
                tools.copy_to(env.SVN_IR / '0000_HNB_SW_IR_.xlsm', root)
            except PermissionError:
                pass

        if not any(file.endswith('.pptx') for file in os.listdir(root)):
            try:
                tools.copy_to(env.SVN_HISTORY / '0000_변경내역서 양식.pptx', root)
            except PermissionError:
                pass
        return

    def __getitem__(self, item):
        return self.Root / item

    def __str__(self) -> str:
        indent = max(len(path) for path in self.__slots__)
        return "\n".join(f'{path:>{indent}}: {self.__getattribute__(path)}' for path in self.__slots__)

    @property
    def change_history(self) -> str:
        for file in os.listdir(self.Root):
            if file.endswith('.pptx'):
                return os.path.join(self.Root, file)
        raise FileExistsError('변경 내역서 없음')

