# 入门

## 1. 下载数据

下载并解压到文件夹中 [VHP_M_CT_Head.zip](https://drive.google.com/file/d/1bBGpt5pQ0evr-0-f4KDNRnKPoUYj2bJ-/view?usp=drive_link)  
数据来自 [Visible Human Project (VHP)](https://www.nlm.nih.gov/research/visible/visible_human.html)这是一个男性头部的 CT 扫描图像

## 2. 导入为「数据层」

给立方体添加几何节点，并打开几何节点界面侧边栏。切换到 Bioxel Nodes 分页（1），点击 Import Data 按钮（2），在文件选择对话框中，选择数据文件夹中任意一个`.dcm`文件（3），点击 Import Data 按钮（4）

![](assets/import-data.png)

依次会弹出两个对话框，都点击 OK 按钮，等待数据导入（可查看 Blender 界面右下角状态栏的进度条）成功后可以看到 Bioxel Nodes 侧边栏多了数据预览画面。点击下方的 Add 按钮（1），鼠标移动到节点面板，放置 **O Layer** 节点（2）

![](assets/add-o-layer.png)

数据的导入就完成啦👍

数据缓存在主目录里，以「数据层（Layer）」形式添加在 Blender 文件中，「数据层」通过 **O Layer** 节点装载到几何节点。它们的关系如下:

数据缓存 -> 数据层 -> O Layer


## 3. 提取并渲染「结构体」

对「数据层」的操作通过 O Bioxel 系列几何节点完成。

我们需要额外两个节点，**O Cutout by Threshold** 和 **O Realize Structure** 节点（它们都在节点菜单，Add > O Bioxel > Structure 下），并按下图连接：

![](assets/connect-nodes.png)

如果成功，可以看到视图中出现了灰色的头部。接下来我们调整节点参数：

- **O Layer**：勾选 Center，取消 Resample
- **O Cutout by Threshold**：Threshold 设置为 90
- **O Realize Structure**：Density 设置为 40，勾选 Surface

调整物体转向、灯位置，设置渲染器为 Cycles，最终效果如下图：

![](assets/adjust-nodes.png)

这样我们就完成了头部 CT 数据的体积渲染👍

简单捋一下执行逻辑，「数据层」先被剪出（Cutout）为「结构体」。「结构体」顾名思义就是负责储存生物组织结构的对象，但它本身数据类型是体积，并不能直接被看到。需要 **O Realize Structure** 来呈现「结构体」

## 4. 另存数据缓存（可选）

由于数据缓存只是以链接形式保存在 Blender 文件中，所以只传递 Blender 文件给其他设备，会导致「数据层」遗失缓存。点击 Bioxel Nodes 分页中 Save 按钮，选择数据缓存的另存位置来管理缓存资源。

就像图片一样，传递时把数据缓存和 Blender 文件一起发送。
