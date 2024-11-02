import math
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
from PIL import Image, ImageDraw
from PIL.Image import Image as IMG
from PIL.Image import Resampling, Transform, Transpose
from PIL.ImageColor import getrgb
from PIL.ImageDraw import ImageDraw as Draw
from PIL.ImageFilter import Filter

import skia

from .gradient import Gradient
from .text2image import DEFAULT_FALLBACK_FONTS, Text2Image
from .typing import (
    BoxType,
    ColorType,
    DirectionType,
    DistortType,
    FontStyle,
    HAlignType,
    ModeType,
    PointsType,
    PosTypeFloat,
    PosTypeInt,
    SizeType,
    SkiaFontStyle,
    SkiaPaint,
    SkiaTextAlign,
    VAlignType,
    XYType,
)


class BuildImage:
    def __init__(self, image: IMG):
        self.image = image

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height

    @property
    def size(self) -> SizeType:
        return self.image.size

    @property
    def mode(self) -> ModeType:
        return self.image.mode  # type: ignore

    @property
    def draw(self) -> Draw:
        return ImageDraw.Draw(self.image)

    @classmethod
    def new(
        cls, mode: ModeType, size: SizeType, color: Optional[ColorType] = None
    ) -> "BuildImage":
        return cls(Image.new(mode, size, color))  # type: ignore

    @classmethod
    def open(cls, file: Union[str, BytesIO, Path]) -> "BuildImage":
        return cls(Image.open(file))

    def copy(self) -> "BuildImage":
        return BuildImage(self.image.copy())

    def resize(
        self,
        size: SizeType,
        resample: Resampling = Resampling.LANCZOS,
        keep_ratio: bool = False,
        inside: bool = False,
        direction: DirectionType = "center",
        bg_color: Optional[ColorType] = None,
        **kwargs,
    ) -> "BuildImage":
        """
        调整图片尺寸

        :参数:
          * ``size``: 期望图片大小
          * ``keep_ratio``: 是否保持长宽比，默认为 `False`
          * ``inside``: `keep_ratio` 为 `True` 时，
                        若 `inside` 为 `True`，
                        则调整图片大小至包含于期望尺寸，不足部分设为指定颜色；
                        若 `inside` 为 `False`，
                        则调整图片大小至包含期望尺寸，超出部分裁剪
          * ``direction``: 调整图片大小时图片的方位；默认为居中
          * ``bg_color``: 不足部分设置的颜色
        """
        width, height = size
        if keep_ratio:
            if inside:
                ratio = min(width / self.width, height / self.height)
            else:
                ratio = max(width / self.width, height / self.height)
            width = int(self.width * ratio)
            height = int(self.height * ratio)

        image = BuildImage(
            self.image.resize((width, height), resample=resample, **kwargs)
        )

        if keep_ratio:
            image = image.resize_canvas(size, direction, bg_color)
        return image

    def resize_canvas(
        self,
        size: SizeType,
        direction: DirectionType = "center",
        bg_color: Optional[ColorType] = None,
    ) -> "BuildImage":
        """
        调整“画布”大小，超出部分裁剪，不足部分设为指定颜色

        :参数:
          * ``size``: 期望图片大小
          * ``direction``: 调整图片大小时图片的方位；默认为居中
          * ``bg_color``: 不足部分设置的颜色
        """
        w, h = size
        x = int((w - self.width) / 2)
        y = int((h - self.height) / 2)
        if direction in ["north", "northwest", "northeast"]:
            y = 0
        elif direction in ["south", "southwest", "southeast"]:
            y = h - self.height
        if direction in ["west", "northwest", "southwest"]:
            x = 0
        elif direction in ["east", "northeast", "southeast"]:
            x = w - self.width
        image = BuildImage.new(self.mode, size, bg_color)
        image.paste(self.image, (x, y))
        return image

    def resize_width(self, width: int, **kwargs) -> "BuildImage":
        """调整图片宽度，不改变长宽比"""
        return self.resize((width, int(self.height * width / self.width)), **kwargs)

    def resize_height(self, height: int, **kwargs) -> "BuildImage":
        """调整图片高度，不改变长宽比"""
        return self.resize((int(self.width * height / self.height), height), **kwargs)

    def rotate(
        self,
        angle: float,
        resample: Resampling = Resampling.BICUBIC,
        expand: bool = False,
        **kwargs,
    ) -> "BuildImage":
        """旋转图片"""
        image = BuildImage(
            self.image.rotate(angle, resample=resample, expand=expand, **kwargs)
        )
        return image

    def square(self) -> "BuildImage":
        """将图片裁剪为方形"""
        length = min(self.width, self.height)
        return self.resize_canvas((length, length))

    def circle(self) -> "BuildImage":
        """将图片裁剪为圆形"""
        image = self.square().image.convert("RGBA")
        skia_image = skia.Image.frombytes(
            image.convert("RGBA").tobytes(),
            image.size,  # type: ignore
            skia.kRGBA_8888_ColorType,
        )
        surface = skia.Surfaces.MakeRasterN32Premul(image.width, image.height)
        canvas = surface.getCanvas()
        canvas.clear(skia.Color4f.kTransparent)
        path = skia.Path()
        radius = image.width / 2
        path.addCircle(radius, radius, radius)
        canvas.clipPath(path, doAntiAlias=True)
        canvas.drawImage(skia_image, 0, 0)
        surface.flushAndSubmit()
        skia_image = surface.makeImageSnapshot()
        pil_image = Image.fromarray(
            skia_image.convert(
                colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType
            )
        ).convert("RGBA")
        return BuildImage(pil_image)

    def circle_corner(self, r: float) -> "BuildImage":
        """将图片裁剪为圆角矩形"""
        image = self.image.convert("RGBA")
        skia_image = skia.Image.frombytes(
            image.convert("RGBA").tobytes(),
            image.size,  # type: ignore
            skia.kRGBA_8888_ColorType,
        )
        surface = skia.Surfaces.MakeRasterN32Premul(image.width, image.height)
        canvas = surface.getCanvas()
        canvas.clear(skia.Color4f.kTransparent)
        path = skia.Path()
        path.addRoundRect(skia.Rect.MakeWH(image.width, image.height), r, r)
        canvas.clipPath(path, doAntiAlias=True)
        canvas.drawImage(skia_image, 0, 0)
        surface.flushAndSubmit()
        skia_image = surface.makeImageSnapshot()
        pil_image = Image.fromarray(
            skia_image.convert(
                colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType
            )
        ).convert("RGBA")
        return BuildImage(pil_image)

    def crop(self, box: BoxType) -> "BuildImage":
        """裁剪图片"""
        return BuildImage(self.image.crop(box))

    def convert(self, mode: ModeType, **kwargs) -> "BuildImage":
        return BuildImage(self.image.convert(mode, **kwargs))

    def paste(
        self,
        img: Union[IMG, "BuildImage"],
        pos: PosTypeInt = (0, 0),
        alpha: bool = False,
        below: bool = False,
    ) -> "BuildImage":
        """
        粘贴图片

        :参数:
          * ``img``: 待粘贴的图片
          * ``pos``: 粘贴位置
          * ``alpha``: 图片背景是否为透明
          * ``below``: 是否粘贴到底层
        """
        if isinstance(img, BuildImage):
            img = img.image
        new_img = Image.new(self.mode, self.size) if below else self.image.copy()
        if alpha:
            img = img.convert("RGBA")
            new_img.paste(img, pos, mask=img)
        else:
            new_img.paste(img, pos)
        if below:
            new_img.paste(self.image, mask=self.image if self.mode == "RGBA" else None)
        self.image = new_img
        return self

    def alpha_composite(
        self,
        img: Union[IMG, "BuildImage"],
        dest: PosTypeInt = (0, 0),
        source: Union[PosTypeInt, BoxType] = (0, 0),
    ) -> "BuildImage":
        if isinstance(img, BuildImage):
            img = img.image
        return BuildImage(self.image.alpha_composite(img, dest=dest, source=source))  # type: ignore

    def filter(self, filter: Union[Filter, type[Filter]]) -> "BuildImage":
        """滤波"""
        return BuildImage(self.image.filter(filter))

    def transpose(self, method: Transpose) -> "BuildImage":
        """变换"""
        return BuildImage(self.image.transpose(method))

    def perspective(self, points: PointsType) -> "BuildImage":
        """
        透视变换

        :参数:
          * ``points``: 变换后点的位置，顺序依次为：左上->右上->右下->左下
        """

        def find_coeffs(pa: PointsType, pb: PointsType):
            matrix = []
            for p1, p2 in zip(pa, pb):
                matrix.append(
                    [p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]]
                )
                matrix.append(
                    [0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]]
                )
            A = np.matrix(matrix, dtype=np.float32)
            B = np.array(pb).reshape(8)
            res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
            return np.array(res).reshape(8)

        img_w, img_h = self.size
        points_w = [p[0] for p in points]
        points_h = [p[1] for p in points]
        new_w = int(max(points_w) - min(points_w))
        new_h = int(max(points_h) - min(points_h))
        p = ((0, 0), (img_w, 0), (img_w, img_h), (0, img_h))
        coeffs = list(find_coeffs(points, p))
        return BuildImage(
            self.image.transform(
                (new_w, new_h), Transform.PERSPECTIVE, coeffs, Resampling.BICUBIC
            )
        )

    def gradient_color(self, gradient: Gradient) -> "BuildImage":
        """
        渐变色

        :参数:
          * ``gradient``: 渐变对象
        """
        return BuildImage(gradient.create_image(self.size))

    def motion_blur(self, angle: float = 0, degree: int = 0) -> "BuildImage":
        """
        运动模糊

        :参数:
          * ``angle``: 运动方向
          * ``degree``: 模糊程度
        """
        if degree == 0:
            return self.copy()
        matrix = cv2.getRotationMatrix2D((degree / 2, degree / 2), angle + 45, 1)
        kernel = np.diag(np.ones(degree))
        kernel = cv2.warpAffine(kernel, matrix, (degree, degree)) / degree  # type: ignore
        blurred = cv2.filter2D(np.asarray(self.image), -1, kernel)
        cv2.normalize(blurred, blurred, 0, 255, cv2.NORM_MINMAX)
        return BuildImage(Image.fromarray(np.array(blurred, dtype=np.uint8)))

    def distort(self, coefficients: DistortType) -> "BuildImage":
        """
        畸变

        :参数:
          * ``coefficients``: 畸变参数
        """
        res = cv2.undistort(
            np.asarray(self.image),
            np.array([[100, 0, self.width / 2], [0, 100, self.height / 2], [0, 0, 1]]),
            np.asarray(coefficients),
        )
        return BuildImage(Image.fromarray(np.array(res, dtype=np.uint8)))

    def color_mask(self, color: ColorType) -> "BuildImage":
        """
        颜色滤镜，改变图片色调

        :参数:
          * ``color``: 目标颜色
        """
        img = self.image.convert("RGB")
        w, h = img.size
        img_array = np.asarray(img)
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        img_hsl = cv2.cvtColor(img_array, cv2.COLOR_RGB2HLS)
        img_new = np.zeros((h, w, 3), np.uint8)

        if isinstance(color, str):
            color = getrgb(color)
        r = color[0]
        g = color[1]
        b = color[2]
        rgb_sum = sum(color)
        for i in range(h):
            for j in range(w):
                value = int(img_gray[i, j])
                new_color = (
                    [
                        int(value * r / rgb_sum),
                        int(value * g / rgb_sum),
                        int(value * b / rgb_sum),
                    ]
                    if rgb_sum
                    else [0, 0, 0]
                )
                img_new[i, j] = new_color
        img_new_hsl = cv2.cvtColor(img_new, cv2.COLOR_RGB2HLS)
        result = np.dstack(
            (img_new_hsl[:, :, 0], img_hsl[:, :, 1], img_new_hsl[:, :, 2])
        )
        result = cv2.cvtColor(result, cv2.COLOR_HLS2RGB)
        return BuildImage(Image.fromarray(result))

    def draw_point(
        self, pos: PosTypeFloat, fill: Optional[ColorType] = None
    ) -> "BuildImage":
        """在图片上画点"""
        self.draw.point(pos, fill=fill)
        return self

    def draw_line(
        self,
        xy: XYType,
        fill: Optional[ColorType] = None,
        width: int = 1,
    ) -> "BuildImage":
        """在图片上画直线"""
        self.draw.line(xy, fill=fill, width=width)
        return self

    def draw_rectangle(
        self,
        xy: XYType,
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: int = 1,
    ) -> "BuildImage":
        """在图片上画矩形"""
        self.draw.rectangle(xy, fill, outline, width)
        return self

    def draw_rounded_rectangle(
        self,
        xy: XYType,
        radius: int = 0,
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: int = 1,
    ) -> "BuildImage":
        """在图片上画圆角矩形"""
        self.draw.rounded_rectangle(xy, radius, fill, outline, width)
        return self

    def draw_polygon(
        self,
        xy: list[PosTypeFloat],
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: int = 1,
    ) -> "BuildImage":
        """在图片上画多边形"""
        self.draw.polygon(xy, fill, outline, width)
        return self

    def draw_arc(
        self,
        xy: XYType,
        start: float,
        end: float,
        fill: Optional[ColorType] = None,
        width: int = 1,
    ) -> "BuildImage":
        """在图片上画圆弧"""
        self.draw.arc(xy, start, end, fill, width)
        return self

    def draw_ellipse(
        self,
        xy: XYType,
        fill: Optional[ColorType] = None,
        outline: Optional[ColorType] = None,
        width: int = 1,
    ) -> "BuildImage":
        """在图片上画圆"""
        self.draw.ellipse(xy, fill, outline, width)
        return self

    def draw_text(
        self,
        xy: Union[PosTypeFloat, XYType],
        text: str,
        *,
        font_size: int = 16,
        max_fontsize: int = 30,
        min_fontsize: int = 12,
        allow_wrap: bool = False,
        font_style: Union[FontStyle, SkiaFontStyle] = "normal",
        fill: Union[ColorType, SkiaPaint] = "black",
        halign: HAlignType = "center",
        valign: VAlignType = "center",
        lines_align: Union[HAlignType, SkiaTextAlign] = "left",
        stroke_ratio: float = 0.02,
        stroke_fill: Optional[ColorType] = None,
        font_families: list[str] = [],
        fallback_fonts_families: list[str] = DEFAULT_FALLBACK_FONTS,
    ) -> "BuildImage":
        """
        在图片上指定区域画文字

        :参数:
          * ``xy``: 文字位置或文字区域；
                    传入 4 个参数时为文字区域，顺序依次为 左，上，右，下
          * ``text``: 文字，支持多行
          * ``font_size``: 字体大小
          * ``max_fontsize``: 允许的最大字体大小
          * ``min_fontsize``: 允许的最小字体大小
          * ``allow_wrap``: 是否允许折行
          * ``font_style``: 字体样式，默认为 "normal"
          * ``fill``: 文字颜色，默认为 `black`
          * ``halign``: 横向对齐方式，默认为 `center`
          * ``valign``: 纵向对齐方式，默认为 `center`
          * ``lines_align``: 多行文字对齐方式，默认为 `left`
          * ``stroke_ratio``: 文字描边的比例，即 描边宽度 / 字体大小
          * ``stroke_fill``: 描边颜色
          * ``font_families``: 指定首选字体
          * ``fallback_fonts_families``: 指定备选字体
        """

        if len(xy) == 2:
            text2img = Text2Image.from_text(
                text,
                font_size,
                font_style=font_style,
                fill=fill,
                align=lines_align,
                stroke_width=round(font_size * stroke_ratio),
                stroke_fill=stroke_fill,
                font_families=font_families,
                fallback_fonts_families=fallback_fonts_families,
            )
            text2img.draw_on_image(self.image, xy)
            return self

        left = xy[0]
        top = xy[1]
        width = xy[2] - xy[0]
        height = xy[3] - xy[1]
        font_size = max_fontsize
        while True:
            text2img = Text2Image.from_text(
                text,
                font_size,
                font_style=font_style,
                fill=fill,
                align=lines_align,
                stroke_width=round(font_size * stroke_ratio),
                stroke_fill=stroke_fill,
                font_families=font_families,
                fallback_fonts_families=fallback_fonts_families,
            )
            text_w = text2img.longest_line
            text2img.wrap(math.ceil(text_w))
            text_h = text2img.height
            if text_w > width and allow_wrap:
                text2img.wrap(width)
                text_w = text2img.longest_line
                text_h = text2img.height
            if text_w > width or text_h > height:
                font_size -= 1
                if font_size < min_fontsize:
                    raise ValueError("在指定的区域内画不下这段文字")
            else:
                x = left  # "left"
                if halign == "center":
                    x += (width - text_w) / 2
                elif halign == "right":
                    x += width - text_w

                y = top  # "top"
                if valign == "center":
                    y += (height - text_h) / 2
                elif valign == "bottom":
                    y += height - text_h

                text2img.draw_on_image(self.image, (x, y))
                return self

    def draw_bbcode_text(
        self,
        xy: Union[PosTypeFloat, XYType],
        text: str,
        *,
        font_size: int = 16,
        max_fontsize: int = 30,
        min_fontsize: int = 12,
        allow_wrap: bool = False,
        fill: ColorType = "black",
        halign: HAlignType = "center",
        valign: VAlignType = "center",
        lines_align: HAlignType = "left",
        stroke_ratio: float = 0.02,
        stroke_fill: Optional[ColorType] = None,
        font_families: list[str] = [],
        fallback_fonts_families: list[str] = DEFAULT_FALLBACK_FONTS,
    ) -> "BuildImage":
        """
        在图片上指定区域画文字

        :参数:
          * ``xy``: 文字位置或文字区域；
                    传入 4 个参数时为文字区域，顺序依次为 左，上，右，下
          * ``text``: 文字，支持多行
          * ``font_size``: 字体大小
          * ``max_fontsize``: 允许的最大字体大小
          * ``min_fontsize``: 允许的最小字体大小
          * ``allow_wrap``: 是否允许折行
          * ``fill``: 文字颜色，默认为 `black`
          * ``halign``: 横向对齐方式，默认为 `center`
          * ``valign``: 纵向对齐方式，默认为 `center`
          * ``lines_align``: 多行文字对齐方式，默认为 `left`
          * ``stroke_ratio``: 文字描边的比例，即 描边宽度 / 字体大小
          * ``stroke_fill``: 描边颜色
          * ``font_families``: 指定首选字体
          * ``fallback_fonts_families``: 指定备选字体
        """

        if len(xy) == 2:
            text2img = Text2Image.from_bbcode_text(
                text,
                font_size,
                fill=fill,
                align=lines_align,
                stroke_ratio=stroke_ratio,
                stroke_fill=stroke_fill,
                font_families=font_families,
                fallback_fonts_families=fallback_fonts_families,
            )
            text2img.draw_on_image(self.image, xy)
            return self

        left = xy[0]
        top = xy[1]
        width = xy[2] - xy[0]
        height = xy[3] - xy[1]
        font_size = max_fontsize
        while True:
            text2img = Text2Image.from_bbcode_text(
                text,
                font_size,
                fill=fill,
                align=lines_align,
                stroke_ratio=stroke_ratio,
                stroke_fill=stroke_fill,
                font_families=font_families,
                fallback_fonts_families=fallback_fonts_families,
            )
            text_w = text2img.longest_line
            text2img.wrap(math.ceil(text_w))
            text_h = text2img.height
            if text_w > width and allow_wrap:
                text2img.wrap(width)
                text_w = text2img.longest_line
                text_h = text2img.height
            if text_w > width or text_h > height:
                font_size -= 1
                if font_size < min_fontsize:
                    raise ValueError("在指定的区域内画不下这段文字")
            else:
                x = left  # "left"
                if halign == "center":
                    x += (width - text_w) / 2
                elif halign == "right":
                    x += width - text_w

                y = top  # "top"
                if valign == "center":
                    y += (height - text_h) / 2
                elif valign == "bottom":
                    y += height - text_h

                text2img.draw_on_image(self.image, (x, y))
                return self

    def save(self, format: str, **params) -> BytesIO:
        output = BytesIO()
        self.image.save(output, format, **params)
        return output

    def save_jpg(self, bg_color: ColorType = "white") -> BytesIO:
        """
        保存图片为 jpg 格式

        :参数:
          * ``bg_color``: 由 png 转为 jpg 时的背景颜色，默认为白色
        """
        if self.mode == "RGBA":
            img = self.new("RGBA", self.size, bg_color)
            img.paste(self.image, alpha=True)
        else:
            img = self
        return img.convert("RGB").save("jpeg")

    def save_png(self) -> BytesIO:
        """保存图片为 png 格式"""
        return self.convert("RGBA").save("png")
