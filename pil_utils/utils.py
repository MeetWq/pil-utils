from PIL.ImageColor import getrgb

import skia
from skia import textlayout

from .typing import ColorType, FontStyle, HAlignType


def to_skia_text_align(align: HAlignType) -> textlayout.TextAlign:  # type: ignore
    if align == "center":
        return textlayout.TextAlign.kCenter
    elif align == "right":
        return textlayout.TextAlign.kRight
    return textlayout.TextAlign.kLeft


def to_skia_color(color: ColorType) -> skia.Color4f:
    if isinstance(color, str):
        color = getrgb(color)
    if len(color) == 3:
        color = (color[0], color[1], color[2], 255)
    return skia.Color4f(color[0] / 255, color[1] / 255, color[2] / 255, color[3] / 255)


def to_skia_font_style(font_style: FontStyle) -> skia.FontStyle:
    if font_style == "bold":
        return skia.FontStyle.Bold()
    elif font_style == "italic":
        return skia.FontStyle.Italic()
    elif font_style == "bold_italic":
        return skia.FontStyle.BoldItalic()
    return skia.FontStyle.Normal()
