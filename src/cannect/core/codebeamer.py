# pip install playwright && playwright install
from cannect.config import env
from cannect.errors import CodeBeamerError
from functools import cached_property
from pandas import DataFrame
from playwright.async_api import async_playwright
from typing import Union
import re
import html


def _line_clear(text:str):
    def __remove_brackets(_txt_):
        _new_, n_bracket = str(_txt_), None
        for n, c in enumerate(_txt_):
            if c == "(":
                n_bracket = 1 if (n_bracket is None) else n_bracket + 1
            if c == ")":
                n_bracket -= 1
            if n_bracket == 0:
                return _new_[n + 1:].strip()
        return _new_.strip()

    if text.startswith("|"):
        text = __remove_brackets(text)

    if "%%" in text:
        new = []
        for frac in text.split("%%"):
            if frac.strip().startswith("("):
                frac = __remove_brackets(frac)
            if frac.endswith("%!"):
                frac = frac.replace("%!", "")
            new.append(frac)
        text = "".join(new)
    return text

def md2table(text: str) -> DataFrame:
    """

    """
    lines = text.splitlines()
    rows, cols = [], []
    for n, line in enumerate(lines):
        src = _line_clear(line)
        if line.startswith("|"):
            cols.append(src)
        else:
            if cols:
                cols[-1] += f'\n{src}'

        if not line:
            if cols:
                rows.append(cols)
                cols = []

    rows.append(cols)

    if not all(rows[0]):
        rows.remove(rows[0])

    return DataFrame(data=rows[1:], columns=rows[0])


def normalize_codebeamer_text(raw: str) -> str:
    text = raw.replace("\r\n", "\n")

    # 1) HTML entity 해제
    text = html.unescape(text)

    # 2) 줄바꿈 표기 정리
    text = text.replace("\\\\", "")

    # 3) Codebeamer escape 처리
    text = text \
            .replace("~_", "_") \
            .replace("~,", ",") \
            .replace("~-", "-") \
            .replace("~>", ">") \
            .replace("~%", "%") \
            .replace("~[", "[") \
            .replace("~]", "]") \
            .replace("~(", "(") \
            .replace("~)", ")") \
            .replace("~:", ":") \
            .replace("~*", "*")

        # 4) 이미지 마크업 제거: [!....!]
    text = re.sub(r"\[!.*?!\]", "", text, flags=re.DOTALL)

    text = "\n".join([
        _line_clear(line.strip()) for line in text.split("\n")
    ])

    # 5) 테이블 블록 제거 또는 단순화
    if "[{Table" in text:
        pattern = r'\[\{Table.*?\}\]'
        matches = re.findall(pattern, text, flags=re.DOTALL)
        table = matches[0] \
                .replace("\r\n", "\n") \
                .replace("}]", "")
        text = text.replace(matches[0], md2table(table).to_string(index=False))

    return "\n".join([line for line in text.splitlines() if line])


class CodeBeamer:

    @classmethod
    async def cache(cls, user_id: str, user_pw: str, headless: bool = False):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto("https://ade-cb.hmckmc.co.kr/cb/login.spr")

            id_selector = "#user"
            pw_selector = "#password"

            await page.wait_for_selector(id_selector, timeout=10000)
            await page.fill(id_selector, user_id)
            await page.fill(pw_selector, user_pw)
            await page.press(pw_selector, "Enter")

            await page.wait_for_url(lambda url: "login.spr" not in url, timeout=15000)

            await context.storage_state(path=str(env.CB_AUTH))
            await browser.close()

    @classmethod
    async def _request_fields(cls, item: Union[int, str]) -> dict | None:
        if not env.CB_AUTH.exists():
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=str(env.CB_AUTH))
            response = await context.request.get(
                f"https://ade-cb.hmckmc.co.kr/cb/api/v3/items/{item}/fields"
            )

            if response.status == 200:
                data = await response.json()
                await browser.close()
                return data
            if response.status == 404:
                raise CodeBeamerError(f'no such item {item} in CodeBeamer')

            await browser.close()
            return None

    @classmethod
    async def get_field(cls, item: Union[int, str], user_id: str = None, user_pw: str = None) -> dict:
        src = await cls._request_fields(item)
        if src is not None:
            return src

        if user_id is None or user_pw is None:
            raise ConnectionError("세션이 없거나 만료되었습니다. user_id/user_pw가 필요합니다.")

        await cls.cache(user_id=user_id, user_pw=user_pw, headless=True)

        src = await cls._request_fields(item)
        if src is None:
            raise ConnectionError("unable to connect codebeamer after re-login")

        return src

    @classmethod
    async def create(cls, item: Union[int, str], **kwargs):
        self = cls.__new__(cls)
        self.item = item

        src = await cls.get_field(item, **kwargs)

        try:
            self._readonly = rd = DataFrame(data=src['readOnlyFields'])
            self._editable = ed = DataFrame(data=src['editableFields'])

            self.kind = cls._search(rd, name='Tracker')
            self.submitted_by = cls._search(rd, name='Submitted by')
            self.summary = cls._search(ed, name='Summary')
        except (KeyError, TypeError, Exception) as e:
            raise CodeBeamerError(f'{src}\n{e}')

        return self

    @staticmethod
    def _search(db: DataFrame, field_id: int = None, name: str = None) -> str:
        if field_id is not None:
            get = db[db['fieldId'] == int(field_id)]
        elif name is not None:
            get = db[db['name'] == name]
        else:
            raise KeyError()

        if get.empty:
            return ''

        res = []
        value = get['value'].dropna()
        if not value.empty:
            res += value.tolist()
        values = get['values'].dropna()
        if not values.empty:
            for val in values:
                for v in val:
                    res.append(v['name'])
        return ', '.join(res)

    @cached_property
    def baseline(self) -> str:
        return self._search(self._editable, name="베이스라인")

    @cached_property
    def description(self) -> str:
        return normalize_codebeamer_text(
            self._search(self._editable, name="Description")
        )

    @cached_property
    def lcr_number(self) -> str:
        return self._search(self._editable, name="LCR 번호")

    @cached_property
    def lcr_submitter(self) -> str:
        return self._search(self._editable, name="LCR 발행자")

    @cached_property
    def lcr_submit_dep(self) -> str:
        return self._search(self._editable, name="LCR 발행처")

    @cached_property
    def models(self) -> list:
        get = self._search(self._editable, name="모델").replace(",", " ").strip()
        return [m for m in get.split(" ") if m]

    @cached_property
    def problem(self) -> str:
        return normalize_codebeamer_text(
            self._search(self._editable, name="문제 현상")
        )

    @cached_property
    def cause(self) -> str:
        return normalize_codebeamer_text(
            self._search(self._editable, name="원인")
        )

    @cached_property
    def requirement(self) -> str:
        return normalize_codebeamer_text(
            self._search(self._editable, name="요구사항")
        )

if __name__ == "__main__":
    from pandas import set_option
    set_option('display.expand_frame_repr', False)
    import asyncio

    async def main():
        cb = await CodeBeamer.create(
            # item=18734880, # 특이점 표 존재 Case
            item=19651261, # Text ONLY Case
            user_id=env.CODEBEAMER_ID,
            user_pw=env.CODEBEAMER_PW
        )

        # print(cb.kind)
        # print(cb.summary)
        print(cb.lcr_number)
        print(cb.lcr_submitter)
        print(cb.lcr_submit_dep)
        # print(cb.submitted_by)
        # print(cb.models)
        print(cb.baseline)
        # print(cb.description)
        print(cb.problem)
        print(cb.cause)
        print(cb.requirement)


    asyncio.run(main())
