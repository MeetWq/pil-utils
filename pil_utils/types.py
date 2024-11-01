from typing import Literal, Union

ModeType = Literal[
    "1", "CMYK", "F", "HSV", "I", "L", "LAB", "P", "RGB", "RGBA", "RGBX", "YCbCr"
]
ColorType = Union[str, tuple[int, int, int], tuple[int, int, int, int]]
PosTypeFloat = tuple[float, float]
PosTypeInt = tuple[int, int]
XYType = tuple[float, float, float, float]
BoxType = tuple[int, int, int, int]
PointsType = tuple[PosTypeFloat, PosTypeFloat, PosTypeFloat, PosTypeFloat]
DistortType = tuple[float, float, float, float]
SizeType = tuple[int, int]
HAlignType = Literal["left", "right", "center"]
VAlignType = Literal["top", "bottom", "center"]
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
FontStyle = Literal["normal", "italic", "bold", "bold_italic"]
