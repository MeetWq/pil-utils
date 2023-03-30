## pil-utils


### 功能

- 提供 `BuildImage` 类，方便图片尺寸修改、添加文字等操作
- 提供 `Text2Image` 类，方便实现文字转图，支持少量 `BBCode` 标签
- 文字支持多种字体切换，能够支持 `emoji`
- 添加文字自动调节字体大小


### 配置字体

字体文件需要安装到系统目录下

> **Note**
>
> 安装新字体后若文字仍显示不正常，可删掉 `matplotlib` 字体缓存文件重新运行程序
>
> 缓存文件位置：
> - Windows: `C:\Users\<username>\.matplotlib\fontlist-xxx.json`
> - Linux: `~/.cache/matplotlib/fontlist-xxx.json`
> - Mac: `~/Library/Caches/matplotlib/fontlist-xxx.json`


默认从以下备选字体列表中查找能够显示的字体

```
"Arial", "Tahoma", "Helvetica Neue", "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans SC", "Noto Sans SC", "Noto Sans CJK JP", "WenQuanYi Micro Hei", "Apple Color Emoji", "Noto Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"
```

#### 中文字体 和 emoji字体 安装

根据系统的不同，推荐安装的字体如下：

- Windows:

大部分 Windows 系统自带 [微软雅黑](https://learn.microsoft.com/zh-cn/typography/font-list/microsoft-yahei) 中文字体 和 [Segoe UI Emoji](https://learn.microsoft.com/zh-cn/typography/font-list/segoe-ui-emoji) emoji 字体，一般情况下无需额外安装


- Linux:

部分系统可能自带 [文泉驿微米黑](http://wenq.org/wqy2/index.cgi?MicroHei) 中文字体；

对于 Ubuntu 系统，推荐安装 Noto Sans CJK 和 Noto Color Emoji：

```bash
sudo apt install fonts-noto-cjk fonts-noto-color-emoji
```

为避免 Noto Sans CJK 中部分中文显示为异体（日文）字形，可以将简体中文设置为默认语言（详见 [ArchWiki](https://wiki.archlinux.org/title/Localization/Simplified_Chinese?rdfrom=https%3A%2F%2Fwiki.archlinux.org%2Findex.php%3Ftitle%3DLocalization_%28%25E7%25AE%2580%25E4%25BD%2593%25E4%25B8%25AD%25E6%2596%2587%29%2FSimplified_Chinese_%28%25E7%25AE%2580%25E4%25BD%2593%25E4%25B8%25AD%25E6%2596%2587%29%26redirect%3Dno#%E4%BF%AE%E6%AD%A3%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87%E6%98%BE%E7%A4%BA%E4%B8%BA%E5%BC%82%E4%BD%93%EF%BC%88%E6%97%A5%E6%96%87%EF%BC%89%E5%AD%97%E5%BD%A2)）：

```bash
sudo locale-gen zh_CN zh_CN.UTF-8
sudo update-locale LC_ALL=zh_CN.UTF-8 LANG=zh_CN.UTF-8
fc-cache -fv
```

其他 Linux 系统可以自行下载字体文件安装：

思源黑体：https://github.com/adobe-fonts/source-han-sans

NotoSansSC：https://fonts.google.com/noto/specimen/Noto+Sans+SC

Noto Color Emoji：https://github.com/googlefonts/noto-emoji


- Mac:

苹果系统一般自带 "PingFang SC" 中文字体 与 "Apple Color Emoji" emoji 字体

#### 字体安装方式

不同系统的字体安装方式：

- Windows:
    - 双击通过字体查看器安装
    - 复制到字体文件夹：`C:\Windows\Fonts`

- Linux:

在 `/usr/share/fonts` 目录下新建文件夹，如 `myfonts`，将字体文件复制到该路径下；

运行如下命令建立字体缓存：

```bash
fc-cache -fv
```

- Mac:

使用字体册打开字体文件安装


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
- `[font=Microsoft YaHei][/font]`: 文字字体
- `[size=30][/size]`: 文字大小
- `[b][/b]`: 文字加粗
- `[i][/i]`: 文字斜体
- `[u][/u]`: 文字下划线
- `[del][/del]`: 文字删除线

### 特别感谢

- [HibiKier/zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) 基于 Nonebot2 和 go-cqhttp 开发，以 postgresql 作为数据库，非常可爱的绪山真寻bot
