# 提升性能

体素重建和体素渲染是非常消耗计算资源的，以下是一些提升插件性能的建议。

## 使用低分辨率数据作为预览

体素的分辨率几何倍地影响计算效率，O Layer 的 Resample 开启可以大大提高计算速度。当你需要正式渲染的时候再关闭即可。在 Bioxel Nodes 分页的 Layer Nodes 面板罗列了当前几何节点中添加的所有 O Layer，你可以统一管理是否开启 Resample，以及程度。

## 平衡的渲染设置

我列出了一些对体渲染影响最大的设置，以便您找到最适合自己的平衡点。

- **Light Paths > Max Bounces > Volume** 影响体数据的反弹次数，值越高，体数据看起来越透明。

- **Light Paths > Max Bounces > Transparent** 影响透明表面透射的次数，值越高，透明表面看起来越透明。

- **Volumes > Step Rate Render | Viewport** 影响体渲染的步长，值越小，体数据看起来越精细。

Bioxel Nodes 提供了一些渲染设置预设以便快速配置。点击顶部菜单 **Bioxel Nodes > Render Setting Presets**，包括 Performance（左侧）、Balance（中间）和 Quality（右侧）。以下是它们的比较。

![alt text](assets/render-performance.png)

## 使用 EEVEE 渲染

EEVEE 渲染体数据不如 Cycles，但它确实有渲染体数据的优势，如果您想获得清晰的切片视图，它甚至是更好的选择。EEVEE 的实时渲染使得在 Blender 中创建交互式内容成为可能。