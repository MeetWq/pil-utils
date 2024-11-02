## pil-utils

### 功能

- 提供 `BuildImage` 类，方便图片尺寸修改、添加文字等操作
- 提供 `Text2Image` 类，方便实现文字转图，支持少量 `BBCode` 标签


### 安装

使用 pip 安装：
```
pip install pil-utils
```

插件依赖 [skia-python](https://github.com/kyamagu/skia-python) 来绘制文字，对于 Linux 平台，需要安装 OpenGL 和 fontconfig：
```
apt-get install libfontconfig1 libgl1-mesa-glx libgl1-mesa-dri
```
或：
```
yum install fontconfig mesa-libGL mesa-dri-drivers
```

具体安装说明请参考 [skia-python 文档](https://kyamagu.github.io/skia-python/install.html)


### 使用示例


- `BuildImage`

```python
from pil_utils import BuildImage

# output: BytesIO
output = BuildImage.new("RGBA", (200, 200), "grey").circle().draw_text((0, 0, 200, 200), "测试test😂").save_png()
```

![](https://s2.loli.net/2024/11/01/MDIXRSlag3Ue1rQ.png)


- `Text2Image`

```python
from pil_utils import Text2Image

# img: PIL.Image.Image
img = Text2Image.from_text("@mnixry 🤗", 50).to_image(bg_color="white")
```

![](https://s2.loli.net/2024/11/01/wv52WbyTqJRsadP.png)


- 使用 `BBCode`

```python
from pil_utils import text2image

# img: PIL.Image.Image
img = text2image("N[size=40][color=red]O[/color][/size]neBo[size=40][color=blue]T[/color][/size]\n[align=center]太强啦[/align]")
```

![](https://s2.loli.net/2024/11/01/wf7CtAa1WYuJRsQ.png)


目前支持的 `BBCode` 标签：
- `[align=left|right|center][/align]`: 文字对齐方式
- `[color=#66CCFF|red|black][/color]`: 字体颜色
- `[stroke=#66CCFF|red|black][/stroke]`: 描边颜色
- `[font=Microsoft YaHei][/font]`: 文字字体
- `[size=30][/size]`: 文字大小
- `[b][/b]`: 文字加粗
- `[i][/i]`: 文字斜体
- `[u][/u]`: 文字下划线
- `[del][/del]`: 文字删除线

### 特别感谢

- [HibiKier/zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) 基于 Nonebot2 开发，非常可爱的绪山真寻bot
- [kyamagu/skia-python](https://github.com/kyamagu/skia-python) Python binding to Skia Graphics Library
