---
name: image-half-cut
description: 批量将图片上下对半裁开，保存为带 _上 和 _下 后缀的两张图；适用于用户要求"上下对半裁图""image half cut""split image top bottom"等场景。
version: "1.0.1"
---
version: "1.0.1"
---
# 上下对半裁图 / Image Half Cut

## 什么时候使用

当用户需要把一张或一批图片按高度上下对半裁开，并分别保存为上半部分和下半部分时使用。

典型表达：
- "上下对半裁图"
- "把这批图上下切成两张"
- "image half cut"
- "split image top bottom"
- "后缀分别带上/下"

## 输出规则

默认输出到指定目录，文件名保持原始 stem 和扩展名：
- `原文件名_上.扩展名`
- `原文件名_下.扩展名`

支持格式：`.jpg .jpeg .png .webp .bmp .tif .tiff`

## 推荐做法

优先使用本 skill 附带脚本，必须用系统 Python（`/usr/bin/python3`，已安装 Pillow）：

```bash
/usr/bin/python3 /Users/cider/.proma/agent-workspaces/amazon/skills/image-half-cut/scripts/split_images_half.py /path/to/images -o /path/to/output
```

当前工作目录示例：

```bash
/usr/bin/python3 /Users/cider/.proma/agent-workspaces/amazon/skills/image-half-cut/scripts/split_images_half.py . -o split_output
```

如需覆盖已存在输出文件：

```bash
/usr/bin/python3 /Users/cider/.proma/agent-workspaces/amazon/skills/image-half-cut/scripts/split_images_half.py . -o split_output --overwrite
```

## 实现细节

- 脚本支持单张图片路径或图片文件夹路径。
- 文件夹模式只处理当前目录下的图片，不递归子目录。
- 使用 Pillow（系统 Python 3.9 已安装），`crop((left, top, right, bottom))` 用绝对像素坐标，裁剪精确无误。
- 每张图片自适应读取自身宽高，确保不同尺寸图片各自对半裁切。
- 上半图：`crop((0, 0, width, height // 2))`
- 下半图：`crop((0, height // 2, width, height))`
- 输出打印原始尺寸，方便核对。

## 执行检查

完成后至少验证：
- 输出文件是否存在。
- 上下两张图宽度是否等于原图宽度。
- 上下两张图高度是否均为原图高度的一半；奇数高度时使用整数下取整。

可用 `sips` 验证：

```bash
sips -g pixelWidth -g pixelHeight /path/to/output/image_上.png /path/to/output/image_下.png
```
