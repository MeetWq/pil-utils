import math
import re
from dataclasses import dataclass
from typing import Optional, Union

from bbcode import Parser
from PIL import Image
from PIL.Image import Image as IMG
from PIL.ImageColor import colormap

import skia
from skia import textlayout

from .typing import (
    BoxType,
    ColorType,
    FontStyle,
    HAlignType,
    PosTypeFloat,
    SizeType,
)
from .utils import to_skia_color, to_skia_font_style, to_skia_text_align

DEFAULT_FALLBACK_FONTS: list[str] = [
    "Arial",
    "Tahoma",
    "Helvetica Neue",
    "Segoe UI",
    "PingFang SC",
    "Hiragino Sans GB",
    "Microsoft YaHei",
    "Source Han Sans SC",
    "Noto Sans SC",
    "Noto Sans CJK SC",
    "WenQuanYi Micro Hei",
    "Apple Color Emoji",
    "Noto Color Emoji",
    "Segoe UI Emoji",
    "Segoe UI Symbol",
]

font_collection = textlayout.FontCollection()
font_collection.setDefaultFontManager(skia.FontMgr())

ALIGN_PATTERN = re.compile(r"left|right|center")
css_colors = "|".join(colormap.keys())
COLOR_PATTERN = re.compile(rf"#[a-fA-F0-9]{{6}}|{css_colors}")
STROKE_PATTERN = COLOR_PATTERN
FONT_PATTERN = re.compile(r".+")
SIZE_PATTERN = re.compile(r"\d+")


@dataclass
class Paragraph:
    paragraph: textlayout.Paragraph  # type: ignore
    stroke_paragraph: Optional[textlayout.Paragraph]  # type: ignore
    align: HAlignType

    @property
    def longest_line(self) -> float:
        return self.paragraph.LongestLine

    @property
    def height(self) -> float:
        return self.paragraph.Height

    def wrap(self, width: float):
        self.paragraph.layout(width)
        if self.stroke_paragraph:
            self.stroke_paragraph.layout(width)
        return self


class Text2Image:
    def __init__(self, paragraphs: list[Paragraph]):
        self.paragraphs = paragraphs

    @classmethod
    def from_text(
        cls,
        text: str,
        font_size: float,
        *,
        font_style: FontStyle = "normal",
        fill: ColorType = "black",
        align: HAlignType = "left",
        stroke_width: float = 0,
        stroke_fill: Optional[ColorType] = None,
        font_families: list[str] = [],
        fallback_fonts_families: list[str] = DEFAULT_FALLBACK_FONTS,
    ) -> "Text2Image":
        """
        从文本构建 `Text2Image` 对象

        :参数:
          * ``text``: 文本
          * ``font_size``: 字体大小
          * ``font_style``: 字体样式，默认为 `normal`
          * ``fill``: 文字颜色，默认为 `black`
          * ``align``: 多行文字对齐方式，默认为 `left`
          * ``stroke_width``: 文字描边宽度
          * ``stroke_fill``: 描边颜色
          * ``font_families``: 指定首选字体
          * ``fallback_fonts_families``: 指定备选字体
        """

        para_style = textlayout.ParagraphStyle()
        para_style.setTextAlign(to_skia_text_align(align))

        paint = skia.Paint()
        paint.setAntiAlias(True)
        paint.setColor4f(to_skia_color(fill))

        style = textlayout.TextStyle()
        style.setFontSize(font_size)
        style.setForegroundPaint(paint)
        style.setFontFamilies(font_families + fallback_fonts_families)
        style.setFontStyle(to_skia_font_style(font_style))
        style.setLocale("en")

        builder = textlayout.ParagraphBuilder.make(
            para_style, font_collection, skia.Unicodes.ICU.Make()
        )
        builder.pushStyle(style)
        builder.addText(text)
        paragraph = builder.Build()
        paragraph.layout(math.inf)

        stroke_paragraph = None
        if stroke_width and stroke_fill:
            stroke_paint = skia.Paint()
            stroke_paint.setAntiAlias(True)
            stroke_paint.setColor4f(to_skia_color(stroke_fill))
            stroke_paint.setStyle(skia.Paint.kStroke_Style)
            stroke_paint.setStrokeJoin(skia.Paint.kRound_Join)
            stroke_paint.setStrokeWidth(stroke_width * 2)

            stroke_style = textlayout.TextStyle()
            stroke_style.setFontSize(font_size)
            stroke_style.setForegroundPaint(stroke_paint)
            stroke_style.setFontFamilies(font_families + fallback_fonts_families)
            stroke_style.setFontStyle(to_skia_font_style(font_style))
            stroke_style.setLocale("en")

            stroke_builder = textlayout.ParagraphBuilder.make(
                para_style, font_collection, skia.Unicodes.ICU.Make()
            )
            stroke_builder.pushStyle(stroke_style)
            stroke_builder.addText(text)
            stroke_paragraph = stroke_builder.Build()
            stroke_paragraph.layout(math.inf)

        return cls([Paragraph(paragraph, stroke_paragraph, align)])

    @classmethod
    def from_bbcode_text(
        cls,
        text: str,
        font_size: float,
        *,
        fill: ColorType = "black",
        align: HAlignType = "left",
        stroke_ratio: float = 0.02,
        stroke_fill: Optional[ColorType] = None,
        font_families: list[str] = [],
        fallback_fonts_families: list[str] = DEFAULT_FALLBACK_FONTS,
    ) -> "Text2Image":
        """
        从含有 `BBCode` 的文本构建 `Text2Image` 对象

        目前支持的 `BBCode` 标签：
          * ``[align=left|right|center][/align]``: 文字对齐方式
          * ``[color=#66CCFF|red|black][/color]``: 字体颜色
          * ``[stroke=#66CCFF|red|black][/stroke]``: 描边颜色
          * ``[font=Microsoft YaHei][/font]``: 文字字体
          * ``[size=30][/size]``: 文字大小
          * ``[b][/b]``: 文字加粗
          * ``[i][/i]``: 文字斜体
          * ``[u][/u]``: 文字下划线
          * ``[del][/del]``: 文字删除线

        :参数:
          * ``text``: 文本
          * ``fontsize``: 字体大小
          * ``font_style``: 字体样式，默认为 `normal`
          * ``fill``: 文字颜色，默认为 `black`
          * ``align``: 多行文字对齐方式，默认为 `left`
          * ``stroke_ratio``: 文字描边的比例，即 描边宽度 / 字体大小
          * ``stroke_fill``: 描边颜色
          * ``font_families``: 指定首选字体
          * ``fallback_fonts_families``: 指定备选字体
        """

        def new_builder(text_align: HAlignType) -> textlayout.ParagraphBuilder:  # type: ignore
            para_style = textlayout.ParagraphStyle()
            para_style.setTextAlign(to_skia_text_align(text_align))
            builder = textlayout.ParagraphBuilder.make(
                para_style, font_collection, skia.Unicodes.ICU.Make()
            )
            return builder

        def new_style(
            text_color: ColorType,
            text_font: Optional[str],
            text_size: float,
            text_bold: bool,
            text_italic: bool,
            text_underline: bool,
            text_linethrough: bool,
        ) -> textlayout.TextStyle:  # type: ignore
            paint = skia.Paint()
            paint.setAntiAlias(True)
            paint.setColor4f(to_skia_color(text_color))

            style = textlayout.TextStyle()
            style.setFontSize(text_size)
            style.setForegroundPaint(paint)

            fonts = font_families + fallback_fonts_families
            if text_font:
                fonts.insert(0, text_font)
            style.setFontFamilies(fonts)
            style.setLocale("en")

            if text_bold and text_italic:
                text_style = skia.FontStyle.BoldItalic()
            elif text_bold:
                text_style = skia.FontStyle.Bold()
            elif text_italic:
                text_style = skia.FontStyle.Italic()
            else:
                text_style = skia.FontStyle.Normal()
            style.setFontStyle(text_style)

            if text_underline and text_linethrough:
                text_decoration = textlayout.TextDecoration.kUnderlineLineThrough
            elif text_underline:
                text_decoration = textlayout.TextDecoration.kUnderline
            elif text_linethrough:
                text_decoration = textlayout.TextDecoration.kLineThrough
            else:
                text_decoration = textlayout.TextDecoration.kNoDecoration
            style.setDecoration(text_decoration)
            style.setDecorationMode(textlayout.TextDecorationMode.kThrough)
            style.setDecorationColor(to_skia_color(text_color))
            style.setDecorationThicknessMultiplier(1.5)

            return style

        def new_stroke_paint(text_stroke: ColorType, text_size: float) -> skia.Paint:
            paint = skia.Paint()
            paint.setAntiAlias(True)
            paint.setColor4f(to_skia_color(text_stroke))
            paint.setStyle(skia.Paint.kStroke_Style)
            paint.setStrokeJoin(skia.Paint.kRound_Join)
            width = text_size * stroke_ratio
            paint.setStrokeWidth(width * 2)
            return paint

        paragraphs: list[Paragraph] = []
        builder: Optional[
            tuple[textlayout.ParagraphBuilder, textlayout.ParagraphBuilder]  # type: ignore
        ] = None

        align_stack: list[HAlignType] = []
        color_stack: list[ColorType] = []
        stroke_stack: list[ColorType] = []
        font_stack: list[str] = []
        size_stack: list[int] = []
        bold_stack: list[bool] = []
        italic_stack: list[bool] = []
        underline_stack: list[bool] = []
        linethrough_stack: list[bool] = []
        last_align: HAlignType = align
        has_stroke: bool = False

        def build():
            nonlocal builder
            nonlocal has_stroke
            if builder:
                paragraph = builder[0].Build()
                paragraph.layout(math.inf)
                stroke_paragraph = None
                if has_stroke:
                    stroke_paragraph = builder[1].Build()
                    stroke_paragraph.layout(math.inf)
                has_stroke = False
                builder = None
                paragraphs.append(Paragraph(paragraph, stroke_paragraph, last_align))

        parser = Parser()
        parser.recognized_tags = {}
        parser.add_formatter("align", None)
        parser.add_formatter("color", None)
        parser.add_formatter("stroke", None)
        parser.add_formatter("font", None)
        parser.add_formatter("size", None)
        parser.add_formatter("b", None)
        parser.add_formatter("i", None)
        parser.add_formatter("u", None)
        parser.add_formatter("del", None)

        tokens = parser.tokenize(text)
        for token_type, tag_name, tag_opts, token_text in tokens:
            if token_type == 1:
                if tag_name == "align":
                    if re.fullmatch(ALIGN_PATTERN, tag_opts["align"]):
                        align_stack.append(tag_opts["align"])
                elif tag_name == "color":
                    if re.fullmatch(COLOR_PATTERN, tag_opts["color"]):
                        color_stack.append(tag_opts["color"])
                elif tag_name == "stroke":
                    if re.fullmatch(STROKE_PATTERN, tag_opts["stroke"]):
                        stroke_stack.append(tag_opts["stroke"])
                elif tag_name == "font":
                    if re.fullmatch(FONT_PATTERN, tag_opts["font"]):
                        font_stack.append(tag_opts["font"])
                elif tag_name == "size":
                    if re.fullmatch(SIZE_PATTERN, tag_opts["size"]):
                        size_stack.append(int(tag_opts["size"]))
                elif tag_name == "b":
                    bold_stack.append(True)
                elif tag_name == "i":
                    italic_stack.append(True)
                elif tag_name == "u":
                    underline_stack.append(True)
                elif tag_name == "del":
                    linethrough_stack.append(True)
            elif token_type == 2:
                if tag_name == "align":
                    if align_stack:
                        align_stack.pop()
                elif tag_name == "color":
                    if color_stack:
                        color_stack.pop()
                elif tag_name == "stroke":
                    if stroke_stack:
                        stroke_stack.pop()
                elif tag_name == "font":
                    if font_stack:
                        font_stack.pop()
                elif tag_name == "size":
                    if size_stack:
                        size_stack.pop()
                elif tag_name == "b":
                    if bold_stack:
                        bold_stack.pop()
                elif tag_name == "i":
                    if italic_stack:
                        italic_stack.pop()
                elif tag_name == "u":
                    if underline_stack:
                        underline_stack.pop()
                elif tag_name == "del":
                    if linethrough_stack:
                        linethrough_stack.pop()
            elif token_type == 3:
                build()
            elif token_type == 4:
                text_align = align_stack[-1] if align_stack else align
                text_color = color_stack[-1] if color_stack else fill
                text_stroke = stroke_stack[-1] if stroke_stack else stroke_fill
                text_font = font_stack[-1] if font_stack else None
                text_size = size_stack[-1] if size_stack else font_size
                text_bold = bold_stack[-1] if bold_stack else False
                text_italic = italic_stack[-1] if italic_stack else False
                text_underline = underline_stack[-1] if underline_stack else False
                text_linethrough = linethrough_stack[-1] if linethrough_stack else False

                if text_align != last_align:
                    build()
                    last_align = text_align

                if not token_text:
                    continue

                if not builder:
                    builder = (new_builder(text_align), new_builder(text_align))
                style = new_style(
                    text_color,
                    text_font,
                    text_size,
                    text_bold,
                    text_italic,
                    text_underline,
                    text_linethrough,
                )
                stroke_style = new_style(
                    text_color,
                    text_font,
                    text_size,
                    text_bold,
                    text_italic,
                    text_underline,
                    text_linethrough,
                )
                if stroke_ratio and text_stroke:
                    has_stroke = True
                    stroke_paint = new_stroke_paint(text_stroke, text_size)
                    stroke_style.setForegroundPaint(stroke_paint)
                builder[0].pushStyle(style)
                builder[0].addText(token_text)
                builder[0].pop()
                builder[1].pushStyle(stroke_style)
                builder[1].addText(token_text)
                builder[1].pop()

        build()

        return cls(paragraphs)

    @property
    def longest_line(self) -> float:
        if not self.paragraphs:
            return 0
        return max([para.longest_line for para in self.paragraphs])

    @property
    def height(self) -> float:
        if not self.paragraphs:
            return 0
        return sum([para.height for para in self.paragraphs])

    def wrap(self, width: float) -> "Text2Image":
        for para in self.paragraphs:
            para.wrap(width)
        return self

    def to_image(
        self,
        max_width: Optional[int] = None,
        bg_color: Optional[ColorType] = None,
        padding: Union[SizeType, BoxType] = (0, 0),
    ) -> IMG:
        if len(padding) == 4:
            padding_left, padding_top, padding_right, padding_bottom = padding
        else:
            padding_left = padding_right = padding[0]
            padding_top = padding_bottom = padding[1]

        if not max_width:
            max_width = math.ceil(self.longest_line)
        self.wrap(max_width)
        image_width = max_width + padding_left + padding_right
        image_height = math.ceil(self.height + padding_top + padding_bottom)

        surface = skia.Surfaces.MakeRasterN32Premul(image_width, image_height)
        canvas = surface.getCanvas()
        canvas.clear(to_skia_color(bg_color) if bg_color else skia.Color4f.kTransparent)

        x = padding_left
        y = padding_top
        for para in self.paragraphs:
            if para.stroke_paragraph:
                para.stroke_paragraph.paint(canvas, x, y)
            para.paragraph.paint(canvas, x, y)
            y += para.height

        surface.flushAndSubmit()
        skia_image = surface.makeImageSnapshot()
        pil_image = Image.fromarray(
            skia_image.convert(
                colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType
            )
        )

        return pil_image

    def draw_on_image(
        self, img: IMG, pos: PosTypeFloat, max_width: Optional[int] = None
    ):
        mode = img.mode
        image = skia.Image.frombytes(
            img.convert("RGBA").tobytes(),
            img.size,  # type: ignore
            skia.kRGBA_8888_ColorType,
        )
        surface = skia.Surfaces.MakeRasterN32Premul(image.width(), image.height())
        canvas = surface.getCanvas()
        canvas.drawImage(image, 0, 0)

        if not max_width:
            max_width = math.ceil(self.longest_line)
        self.wrap(max_width)

        x = pos[0]
        y = pos[1]
        for para in self.paragraphs:
            if para.stroke_paragraph:
                para.stroke_paragraph.paint(canvas, x, y)
            para.paragraph.paint(canvas, x, y)
            y += para.height

        surface.flushAndSubmit()
        skia_image = surface.makeImageSnapshot()
        pil_image = Image.fromarray(
            skia_image.convert(
                colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType
            )
        ).convert(mode)
        img.im = pil_image.im.copy()  # type: ignore


def text2image(
    text: str,
    *,
    font_size: float = 30,
    max_width: Optional[int] = None,
    bg_color: ColorType = "white",
    padding: Union[SizeType, BoxType] = (10, 10),
    **kwargs,
) -> IMG:
    """
    文字转图片，支持少量 `BBCode` 标签，具体见 `Text2Image` 类的 `from_bbcode_text` 函数

    :参数:
        * ``text``: 文本
        * ``fontsize``: 字体大小
        * ``max_width``: 图片中文字的最大宽度，不设置则不限宽度
        * ``bg_color``: 图片背景颜色
        * ``padding``: 图片边距
    """
    text2img = Text2Image.from_bbcode_text(text, font_size, **kwargs)
    return text2img.to_image(max_width, bg_color, padding)
