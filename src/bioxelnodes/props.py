from pathlib import Path
import bpy

from .operators.layer import SelectAndFocusNode
from .utils import load_icon
from .layer import get_layer_caches, set_layer_caches


def get_snapshot_icon(cache, z: float):
    cache_id = str(cache["id"])
    shape = (64, 64, 32)
    zidx = int(z * (shape[2] - 1))

    path = Path(bpy.path.abspath(cache["path"]))
    return load_icon(path / f"snapshot_{zidx}.png", f"{cache_id}_{zidx}")


def _bioxel_layer_items(self, context):
    """
    EnumProperty items callback: 从 get_layer_caches 构造枚举项。
    使用 PREVIEWS 加载每个 layer 的 thumbnail_png（如果存在）并返回 icon_id。
    """
    items = []
    caches = get_layer_caches()

    for idx, cache in enumerate(caches):
        cache_id = str(cache["id"])
        name = cache.get("name", f"Layer ?")
        description = cache.get("kind", "?")
        z = cache.get("snapshot_z", 0.5)
        icon = get_snapshot_icon(cache, z)
        # 在这个context下，只能加载无法生成。
        items.append((cache_id, name, description, icon, idx))

    if not items:
        items = [("nothing_found", "No Layers",
                  "No layers found", "QUESTION", 0)]

    return items


def _update_layer_gallery(self, context):
    wm = context.window_manager
    selected_id = getattr(wm, "bioxel_layer_library", None)
    cache = next(
        (c for c in get_layer_caches() if str(c.get("id", "")) == str(selected_id)),
        None,
    )
    z = cache.get("snapshot_z", 0.5) if cache else 0.5
    setattr(wm, "bioxel_snapshot_z", z)


def _update_snapshot_z(self, context):
    """
    update callback for WindowManager.bioxel_thumb_z
    - write a slice PNG from the saved .npy
    - update PREVIEWS entry for the selected layer
    - force template_icon_view to refresh by briefly cycling the EnumProperty value
    - force UI redraw
    """
    wm = context.window_manager
    selected_id = getattr(wm, "bioxel_layer_library", None)

    if not selected_id or selected_id == "nothing_found":
        return

    try:
        selected_id = int(selected_id)
    except Exception:
        return

    caches = get_layer_caches()
    z = getattr(wm, "bioxel_snapshot_z", 0.5)

    for cache in caches:
        if int(cache.get("id", -1)) == selected_id:
            cache["snapshot_z"] = z
            break

    set_layer_caches(caches)


class BIOXEL_Series(bpy.types.PropertyGroup):
    id: bpy.props.StringProperty()  # type: ignore
    label: bpy.props.StringProperty()  # type: ignore


class BIOXEL_UL_layer_nodes(bpy.types.UIList):
    """UIList for O Layer nodes only"""

    bl_idname = "BIOXEL_UL_layer_nodes"

    def filter_items(self, context, data, propname):
        nodes = getattr(data, propname)
        flt_flags = []
        flt_neworder = []

        for node in nodes:
            # 只保留 O Layer 节点
            if (
                hasattr(node, "bl_idname")
                and node.bl_idname.startswith("GeometryNodeGroup")
                and getattr(getattr(node, "node_tree", None), "name", "").startswith(
                    "O Layer"
                )
            ):
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0)
        return flt_flags, flt_neworder

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        node = item
        # 这里只画 O Layer 节点，其他已被 filter_items 过滤
        split = layout.split(factor=0.3, align=True)
        col1 = split.row(align=True)
        col2 = split.row(align=True)
        name_socket = node.inputs["Name"]
        resample_socket = node.inputs["Resample"]
        scale_socket = node.inputs["Bioxel Scale"]
        name = str(node.inputs["Name"].default_value)

        # row.prop(name_socket, "default_value", text="")
        col1.prop(resample_socket, "default_value",
                  icon="UV_DATA", text="", toggle=1)
        col1.prop(scale_socket, "default_value", text="")
        col2.label(text=name)

        op = col2.operator(
            SelectAndFocusNode.bl_idname, text="", icon="RESTRICT_SELECT_OFF", emboss=True
        )
        op.node_name = node.name
