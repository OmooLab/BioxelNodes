# 高级玩法

## 切割「结构体」

「结构体」可以被切割，呈现部分结构，通过 O Cut 系列节点完成。比如按下图添加 **O Cut to Region** 节点并连接，添加任意来自场景的物体作为「区域」，输入到节点：

![](assets/cut-to-region.png)

适当调整作为「区域」物体的位置旋转，可以看到头骨结构被限制在区域范围内。

!!! note
    插件提供快速让物体虚化的功能，在 3D 视图模式下，右键「区域」物体，菜单选择 **Bioxel Nodes > Toggle Phantom**

!!! warning
    切割会增加计算量，影响实时性能，勾选 O Layer 的 Resample 来提高性能



**O Cut Small Parts** 节点，是清理神器，能快速把零碎的结构删除，只干净连续的大结构。但是计算特别耗时，注意性能。

![](assets/cut-small-parts.png)

如果你对几何节点很了解，你也可以通过 **O Cut Structure** 直接定义切割的执行范围，比如下图中，选择切割位置 X 大于 0 的部分。

![](assets/cut-structure.png)


## 「结构体」属性设置

展开 **O Cutout by Threshold** 的 Properties，你可以直接修改各项属性值，但都只能均一设置，我们可以用场类型数据赋予差异。以颜色属性为例，比如直接接入 Position 节点，效果如下：

![](assets/set-color-by-pos.png)

我们还可以把数据层的值映射为颜色渐变，这里需要用到 **O Scalar Layer to Color** 节点（这类转换功能的节点都在节点菜单，Add > O Bioxel > Utilities 下）。调整如下

- **O Cutout by Threshold**：Threshold 设置为 20
- **O Scalar Layer to Color**：From Min 和 From Max 分别设置为 20 和 90

![](assets/scalar-to-color.png)

由于软组织的 CT 值小于骨质，当阈值降低，可以看到除了头骨外，附着的软组织也被呈现了出来。**O Scalar Layer to Color** 的 From Min 和 From Max，定义了颜色从 0~1 的取值范围。因此低值的软组织呈现黑色，高值的骨质呈现白色

我们还可以通过 Blender 5.0+ 的 **Closure** 节点来自定义映射方式。比如连接 **Color Ramp** 节点，把属于软组织的黑区，改为暗红色

![](assets/scalar-to-color-ramp.png)

哒哒！解剖渲染就做好啦👍

其他「结构体」属性也可以按这样的方式调整，除了 **O Scalar Layer to Color**，还有 **O Scalar Layer to Factor** 来转换为 0~1 的单值