from pathlib import Path
from PIL import ImageFont
from functools import lru_cache
from fontTools.ttLib import TTFont
from collections import namedtuple
from PIL.ImageFont import FreeTypeFont
from matplotlib.ft2font import FT2Font
from typing import List, Optional, Set
from matplotlib.font_manager import FontManager, FontProperties

from .types import *

font_manager = FontManager()

default_fallback_fonts: List[str] = [
    "Arial",
    "Tahoma",
    "Helvetica Neue",
    "Segoe UI",
    "PingFang SC",
    "Hiragino Sans GB",
    "Microsoft YaHei",
    "Source Han Sans SC",
    "Noto Sans SC",
    "Noto Sans CJK JP",
    "WenQuanYi Micro Hei",
    "Apple Color Emoji",
    "Noto Color Emoji",
    "Segoe UI Emoji",
    "Segoe UI Symbol",
]


class Font:
    def __init__(self, family: str, fontpath: Path, valid_size: Optional[int] = None):
        self.family = family
        """字体族名字"""
        self.path = fontpath.resolve()
        """字体文件路径"""
        self.valid_size = valid_size
        """某些字体不支持缩放，只能以特定的大小加载"""
        self._glyph_table: Set[int] = set()
        for table in TTFont(self.path, fontNumber=0)["cmap"].tables:  # type: ignore
            for key in table.cmap.keys():
                self._glyph_table.add(key)

    @classmethod
    @lru_cache()
    def find(
        cls,
        family: str,
        style: FontStyle = "normal",
        weight: FontWeight = "normal",
        fallback_to_default: bool = True,
    ) -> "Font":
        """查找插件路径和系统路径下的字体"""
        font = cls.find_special_font(family)
        if font:
            return font
        font = cls.find_pil_font(family)
        if font:
            return font
        filepath = font_manager.findfont(
            FontProperties(family, style=style, weight=weight),  # type: ignore
            fallback_to_default=fallback_to_default,
        )
        font = FT2Font(filepath)
        return cls(font.family_name, Path(font.fname))

    @classmethod
    def find_pil_font(cls, name: str) -> Optional["Font"]:
        """通过 PIL ImageFont 查找系统字体"""
        try:
            font = ImageFont.truetype(name, 20)
            fontpath = Path(str(font.path))
            return cls(name, fontpath)
        except OSError:
            pass

    @classmethod
    def find_special_font(cls, family: str) -> Optional["Font"]:
        """查找特殊字体，主要是不可缩放的emoji字体"""

        SpecialFont = namedtuple("SpecialFont", ["family", "fontname", "valid_size"])
        SPECIAL_FONTS = {
            "Apple Color Emoji": SpecialFont(
                "Apple Color Emoji", "Apple Color Emoji.ttc", 160
            ),
            "Noto Color Emoji": SpecialFont(
                "Noto Color Emoji", "NotoColorEmoji.ttf", 109
            ),
        }

        if family in SPECIAL_FONTS:
            prop = SPECIAL_FONTS[family]
            fontname = prop.fontname
            valid_size = prop.valid_size
            try:
                font = ImageFont.truetype(fontname, valid_size)
                fontpath = Path(str(font.path))
                return cls(family, fontpath, valid_size)
            except OSError:
                pass

    @lru_cache()
    def load_font(self, fontsize: int) -> FreeTypeFont:
        """以指定大小加载字体"""
        return ImageFont.truetype(str(self.path), fontsize, encoding="utf-8")

    @lru_cache()
    def has_char(self, char: str) -> bool:
        """检查字体是否支持某个字符"""
        return ord(char) in self._glyph_table


def get_proper_font(
    char: str,
    style: FontStyle = "normal",
    weight: FontWeight = "normal",
    fontname: Optional[str] = None,
    fallback_fonts: List[str] = [],
) -> Font:
    """
    获取合适的字体，将依次检查备选字体是否支持想要的字符

    :参数:
        * ``char``: 字符
        * ``style``: 字体样式，默认为 "normal"
        * ``weight``: 字体粗细，默认为 "normal"
        * ``fontname``: 可选，指定首选字体
        * ``fallback_fonts``: 可选，指定备选字体
    """
    fallback_fonts = fallback_fonts or default_fallback_fonts.copy()
    if fontname:
        fallback_fonts.insert(0, fontname)

    for family in fallback_fonts:
        try:
            font = Font.find(family, style, weight, fallback_to_default=False)
        except:
            try:
                default_fallback_fonts.remove(family)
            except:
                pass
            continue
        if font.has_char(char):
            return font

    return Font.find("serif", style, weight)
