from pathlib import Path
from typing import AnyStr, Callable, Iterable, List, Union
from xml.etree.ElementTree import Element, ElementTree
from xml.dom import minidom
import os, zipfile, shutil, io, re


def unzip(src: Union[str, Path], to: Union[str, Path] = "") -> bool:
    """
    압축(.zip) 해제
    :param src: 압축파일 경로
    :param to : [optional] 압축파일을 풀 경로
    :return:
    """
    if not to:
        to = os.path.dirname(src)
    else:
        os.makedirs(to, exist_ok=True)

    src = str(src)
    if not os.path.isfile(src):
        raise KeyError(f"src: {src}는 경로가 포함된 파일(Full-Directory)이어야 합니다.")
    if src.endswith('.zip'):
        zip_obj = zipfile.ZipFile(src)
        zip_obj.extractall(to)
    # elif src.endswith('.7z'):
    #     with py7zr.SevenZipFile(src, 'r') as arc:
    #         arc.extractall(path=to)
    else:
        # raise KeyError(f"src: {src}는 .zip 또는 .7z 압축 파일만 입력할 수 있습니다.")
        raise KeyError(f"src: {src}는 .zip 압축 파일만 입력할 수 있습니다.")
    return True

def zip(path:Union[str, Path]):
    name = os.path.basename(path)
    shutil.make_archive(name, "zip", root_dir=path)
    shutil.move(f'{name}.zip', path)
    return

def copy_to(file:Union[str, Path], dst:Union[str, Path]) -> str:
    shutil.copy(file, dst)
    # if '.' in os.path.basename(file):
    #     shutil.copy(file, dst)
    # else:
    #     shutil.move(file, dst)
    return os.path.join(dst, os.path.basename(file))

def find_file(root:Union[str, Path], filename:Union[str, Path]) -> Union[str, List[str]]:
    """
    @filename: 확장자까지 포함한 단일 파일 이름
    """
    found = []
    for _root, _dir, _files in os.walk(root):
        for _file in _files:
            if _file == filename:
                found.append(os.path.join(_root, _file))
    if not found:
        return ""
    if len(found) == 1:
        return found[0]
    return found


def clear(path: str, leave_path: bool = True):
    """
    지정한 경로의 파일 및 하위 디렉토리를 모두 삭제

    :param path: 삭제 대상이 될 폴더 경로
    :param leave_path: True면 폴더를 남기고 내용만 삭제, False면 폴더 자체도 삭제
    """
    if not os.path.exists(path):
        return

    try:
        if leave_path:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        else:
            shutil.rmtree(path)
    except Exception as e:
        print(f"Error occurs while clearing directory: {e}")

def path_abbreviate(path: Union[str, Path]) -> str:
    sep = os.path.sep
    split = str(path).split(sep)
    return f"{sep.join(split[:2])}{sep} ... {sep}{sep.join(split[-3:])}"


class xml:

    @classmethod
    def to_str(cls, xml: Union[Element, ElementTree], xml_declaration: bool = False) -> str:
        """
        xml 요소(태그) 및 그 하위 요소를 소스 문자열로 변환

        :param xml:
        :param xml_declaration:

        :return:
        """
        if isinstance(xml, Element):
            xml = ElementTree(xml)

        stream = io.StringIO()
        xml.write(
            file_or_filename=stream,
            encoding='unicode',
            xml_declaration=False,
            method='xml',
        )
        dom = f'{minidom.parseString(stream.getvalue()).toprettyxml()}' \
            .replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>') \
            .replace("<CodeBlock/>", "<CodeBlock></CodeBlock>") \
            .replace("<Comment/>", "<Comment></Comment>") \
            .replace("ns0:", "") \
            .replace('xmlns:ns0="http://www.w3.org/2000/09/xmldsig#" ', '') \
            .replace('<Signature>', '<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">')
        # if not xml.getroot().tag == 'Specifications':
        dom = "\n".join([l for l in dom.split("\n") if "<" in l or ';' in l or '=' in l or not l.startswith("\t")])        # dom = '\n'.join([line for line in dom.split('\n') if line.strip()])
        if not xml_declaration:
            dom = dom.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '')
        return dom

    @classmethod
    def to_dict(cls, xml:Union[Element, ElementTree], target:str='ascet', depth:str='recursive') -> dict:
        """
        xml 요소(태그) 및 그 하위 요소의 text 및 attribute를 dictionary로 변환

        :param xml:
        :param target:
        :param depth:
        :return:
        """
        if isinstance(xml, Element):
            xml = ElementTree(xml)

        if not depth == 'recursive':
            return xml.getroot().attrib

        attr = {}
        for elem in xml.iter():
            copy = elem.attrib.copy()
            if target == "ascet":
                if elem.tag == 'PhysicalInterval' and 'min' in copy:
                    copy['physMin'] = copy['min']
                    copy['physMax'] = copy['max']
                    del copy['min'], copy['max']
                if elem.tag == 'ImplementationInterval' and 'min' in copy:
                    copy['implMin'] = copy['min']
                    copy['implMax'] = copy['max']
                    del copy['min'], copy['max']

                if (elem.tag == 'Comment' and elem.text is not None) or elem.tag == 'CodeBlock':
                    attr[elem.tag.lower()] = elem.text

            attr.update(copy)
        return attr



class KeywordSearch:
    """
    Dataset에 대한 키워드 검색
    """
    logger:Callable = print
    def __init__(self, *samples):
        self._samples = list(samples)
        return

    def __getitem__(self, item:str)-> str:
        result = self.search(self._samples, item)
        if not result:
            self.logger(f"NOT FOUND: '{item}' IN THE MODEL")
        return result

    @classmethod
    def search(cls, samples: Iterable[str], keyword: str) -> Union[str, List[str]]:
        """
        간단한 와일드카드 검색 함수.
        - '*' 는 0글자 이상 임의의 문자열과 매칭됩니다.
        - 대소문자를 구분하지 않습니다.
        - 결과가 1개이면 str을, 그 외(0개 또는 2개 이상)면 List[str]를 반환합니다.
        """
        samples = list(samples)
        if keyword is None:
            return ""

        kw = keyword.strip()
        regex_fragments = []
        for ch in kw:
            if ch == '*':
                regex_fragments.append(".*")
            else:
                regex_fragments.append(re.escape(ch))
        regex_body = "".join(regex_fragments)
        pattern = re.compile(f"^{regex_body}$", flags=re.IGNORECASE)
        matches = [s for s in samples if pattern.match(s)]
        if not matches:
            return ""
        elif len(matches) == 1:
            return matches[0]
        else:
            return matches