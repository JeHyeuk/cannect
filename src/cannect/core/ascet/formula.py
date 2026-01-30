from cannect.schema.datadictionary import DataDictionary
from xml.etree.ElementTree import ElementTree


def formula_dictionary(filepath:str) -> DataDictionary:
    tree = ElementTree(file=filepath)
    data = DataDictionary()
    for tag in tree.iter('Formula'):
        if tag.get('type') != '5 Parameters':
            continue
        obj = DataDictionary()
        obj.unit = tag.get('unit')
        for n, param in enumerate(tag.iter('Parameter'), start=1):
            obj[f'p{n}'] = param.get('value')

        p1, p2, p3, p4, p5 = float(obj.p1), float(obj.p2), float(obj.p3), float(obj.p4), float(obj.p5)
        if p3 != 0:
            obj.quantization = p2 / p3
            obj.offset = -p4 / p3
        elif p1 != 0:
            obj.quantization = abs(p4 / p1)
            obj.offset = (-p4 * p5 - p2) / p1
        else:
            KeyError(f'Unknown Case For {tag.get("name")}')
        data[tag.get('name')] = obj
    return data


if __name__ == "__main__":
    file = r"D:\ETASData\ASCET6.1\Export\_Formula\HNB_I4GDI_EU7.xml"
    formula = formula_dictionary(file)
    print(formula)
    print(formula.k_q0p000244)