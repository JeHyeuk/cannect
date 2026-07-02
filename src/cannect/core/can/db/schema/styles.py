from docx.document import Document
from docx.styles.styles import Styles
from docx.styles.style import ParagraphStyle
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import RGBColor, Pt, Inches




class CustomStyle:

    def __init__(self, doc:Document):
        self.doc = doc
        return

    @property
    def title(self) -> ParagraphStyle:
        if not "title" in self.doc.styles:
            style = self.doc.styles.add_style("title", WD_PARAGRAPH_ALIGNMENT.CENTER)
            style.font.name = "현대산스 Head"
            style.font.size = Pt(28)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.font.bold = True
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        return self.doc.styles['title']

    @property
    def overview_left(self) -> Styles:
        if not "overview_left" in self.doc.styles:
            style = self.doc.styles.add_style("overview_left", WD_PARAGRAPH_ALIGNMENT.CENTER)
            style.font.name = "현대산스 Text"
            style.font.size = Pt(11)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.font.bold = True
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        return self.doc.styles['overview_left']

    @property
    def overview_right(self) -> Styles:
        if not "overview_right" in self.doc.styles:
            style = self.doc.styles.add_style("overview_right", WD_PARAGRAPH_ALIGNMENT.CENTER)
            style.font.name = "현대산스 Text"
            style.font.size = Pt(10)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.font.bold = False
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        return self.doc.styles['overview_right']

    @property
    def footer(self) -> Styles:
        if not "my_footer" in self.doc.styles:
            style = self.doc.styles.add_style("my_footer", WD_STYLE_TYPE.PARAGRAPH)
            style.font.name = "현대산스 Text"
            style.font.size = Pt(10)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.font.bold = False
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        return self.doc.styles['my_footer']

    @property
    def header_left(self) -> Styles:
        if not "header_left" in self.doc.styles:
            style = self.doc.styles.add_style("header_left", WD_PARAGRAPH_ALIGNMENT.CENTER)
            style.font.name = "현대산스 Text"
            style.font.size = Pt(8)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.font.bold = False
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        return self.doc.styles['header_left']

    @property
    def header_right(self) -> Styles:
        if not "header_right" in self.doc.styles:
            style = self.doc.styles.add_style("header_right", WD_PARAGRAPH_ALIGNMENT.CENTER)
            style.font.name = "현대산스 Text"
            style.font.size = Pt(8)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.font.bold = False
            style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        return self.doc.styles['header_right']