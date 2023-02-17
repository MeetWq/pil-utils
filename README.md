## pil-utils


### 功能

- 提供 `BuildImage` 类，方便图片尺寸修改、添加文字等操作
- 提供 `Text2Image` 类，方便实现文字转图，支持少量 `BBCode` 标签
- 文字支持多种字体切换，能够支持 `emoji`
- 添加文字自动调节字体大小


### 配置字体

字体文件需要安装到系统目录下

默认从以下备选字体列表中查找能够显示的字体

```
"Arial", "Tahoma", "Helvetica Neue", "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans SC", "Noto Sans SC", "Noto Sans CJK JP", "WenQuanYi Micro Hei", "Apple Color Emoji", "Noto Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"
```


> 对于 `Ubuntu` 系统，建议安装 `fonts-noto` 软件包 以支持中文字体和 emoji
>
> 并将简体中文设置为默认语言：（否则会有部分中文显示为异体（日文）字形，详见 [ArchWiki](https://wiki.archlinux.org/title/Localization_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)/Simplified_Chinese_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)#%E4%BF%AE%E6%AD%A3%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87%E6%98%BE%E7%A4%BA%E4%B8%BA%E5%BC%82%E4%BD%93%EF%BC%88%E6%97%A5%E6%96%87%EF%BC%89%E5%AD%97%E5%BD%A2)）
> ```bash
> sudo apt install fonts-noto
> sudo locale-gen zh_CN zh_CN.UTF-8
> sudo update-locale LC_ALL=zh_CN.UTF-8 LANG=zh_CN.UTF-8
> fc-cache -fv
> ```


### 使用示例


- `BuildImage`

```python
from pil_utils import BuildImage

# output: BytesIO
output = BuildImage.new("RGBA", (200, 200), "grey").circle().draw_text((0, 0, 200, 200), "测试test😂").save_png()
```

![](https://s2.loli.net/2023/02/17/oOjw9sSbfDAJvYr.png)


- `Text2Image`

```python
from pil_utils import Text2Image

# img: PIL.Image.Image
img = Text2Image.from_text("@mnixry 🤗", 50).to_image(bg_color="white")
```

![](https://s2.loli.net/2023/02/06/aJTqGwzvsVBSO8H.png)


- 使用 `BBCode`

```python
from pil_utils import text2image

# img: PIL.Image.Image
img = text2image("N[size=40][color=red]O[/color][/size]neBo[size=40][color=blue]T[/color][/size]\n[align=center]太强啦[/align]")
```

![](https://s2.loli.net/2023/02/06/Hfwj67QoVAatexN.png)


目前支持的 `BBCode` 标签：
- `[align=left|right|center][/align]`: 文字对齐方式
- `[color=#66CCFF|red|black][/color]`: 字体颜色
- `[stroke=#66CCFF|red|black][/stroke]`: 描边颜色
- `[font=msyh.ttc][/font]`: 文字字体
- `[size=30][/size]`: 文字大小
- `[b][/b]`: 文字加粗


### 特别感谢

- [HibiKier/zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) 基于 Nonebot2 和 go-cqhttp 开发，以 postgresql 作为数据库，非常可爱的绪山真寻bot
