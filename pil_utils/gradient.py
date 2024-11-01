from PIL import Image
from PIL.Image import Image as IMG

import skia

from .typing import ColorType, SizeType, XYType
from .utils import to_skia_color


class ColorStop:
    def __init__(self, stop: float, color: "ColorType"):
        self.stop = stop
        """介于 0.0 与 1.0 之间的值，表示渐变中开始与结束之间的位置"""
        self.color = color
        """在 stop 位置显示的颜色值"""

    def __lt__(self, other: "ColorStop"):
        return self.stop < other.stop


class Gradient:
    def __init__(self, color_stops: list[ColorStop] = []):
        self.color_stops = color_stops
        self.color_stops.sort()

    def add_color_stop(self, stop: float, color: "ColorType"):
        self.color_stops.append(ColorStop(stop, color))
        self.color_stops.sort()

    def create_image(self, size: "SizeType") -> IMG:
        raise NotImplementedError


class LinearGradient(Gradient):
    def __init__(self, xy: "XYType", color_stops: list[ColorStop] = []):
        self.xy = xy
        self.x0 = xy[0]
        """渐变开始点的 x 坐标"""
        self.y0 = xy[1]
        """渐变开始点的 y 坐标"""
        self.x1 = xy[2]
        """渐变结束点的 x 坐标"""
        self.y1 = xy[3]
        """渐变结束点的 y 坐标"""
        super().__init__(color_stops)

    def create_image(self, size: "SizeType") -> IMG:
        surface = skia.Surfaces.MakeRasterN32Premul(size[0], size[1])
        canvas = surface.getCanvas()
        canvas.clear(skia.Color4f.kTransparent)
        paint = skia.Paint(
            Shader=skia.GradientShader.MakeLinear(
                points=[skia.Point(self.x0, self.y0), skia.Point(self.x1, self.y1)],
                colors=[int(to_skia_color(stop.color)) for stop in self.color_stops],
                positions=[stop.stop for stop in self.color_stops],
            )
        )
        canvas.drawPaint(paint)
        surface.flushAndSubmit()
        skia_image = surface.makeImageSnapshot()
        pil_image = Image.fromarray(
            skia_image.convert(
                colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType
            )
        ).convert("RGBA")
        return pil_image


if __name__ == "__main__":
    img = LinearGradient(
        (0, 0, 255, 255),
        [
            ColorStop(0, "red"),
            ColorStop(0.1, "orange"),
            ColorStop(0.25, "yellow"),
            ColorStop(0.4, "green"),
            ColorStop(0.6, "blue"),
            ColorStop(0.8, "cyan"),
            ColorStop(1, "purple"),
        ],
    ).create_image((255, 255))
    img.save("test.png")
