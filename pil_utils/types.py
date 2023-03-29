from typing import Literal, Tuple, Union

ModeType = Literal[
    "1", "CMYK", "F", "HSV", "I", "L", "LAB", "P", "RGB", "RGBA", "RGBX", "YCbCr"
]
ColorType = Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]
PosTypeFloat = Tuple[float, float]
PosTypeInt = Tuple[int, int]
XYType = Tuple[float, float, float, float]
BoxType = Tuple[int, int, int, int]
PointsTYpe = Tuple[PosTypeFloat, PosTypeFloat, PosTypeFloat, PosTypeFloat]
DistortType = Tuple[float, float, float, float]
SizeType = Tuple[int, int]
HAlignType = Literal["left", "right", "center"]
VAlignType = Literal["top", "bottom", "center"]
OrientType = Literal["horizontal", "vertical"]
DirectionType = Literal[
    "center",
    "north",
    "south",
    "west",
    "east",
    "northwest",
    "northeast",
    "southwest",
    "southeast",
]
FontStyle = Literal["normal", "italic", "oblique"]
FontWeight = Literal["ultralight", "light", "normal", "bold", "ultrabold", "heavy"]
