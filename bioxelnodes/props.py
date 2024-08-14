import bpy

from .bioxelutils.utils import get_node_type


class BIOXELNODES_UL_layer_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.label, translate=False, icon_value=icon)


class BIOXELNODES_Series(bpy.types.PropertyGroup):
    id: bpy.props.StringProperty()   # type: ignore
    label: bpy.props.StringProperty()   # type: ignore


def select_layer(self, context):
    layer_list_UL = bpy.context.window_manager.bioxelnodes_layer_list_UL
    layer_list = layer_list_UL.layer_list
    layer_list_active = layer_list_UL.layer_list_active

    if len(layer_list) > 0 and layer_list_active != -1 and layer_list_active < len(layer_list):
        layer_obj = bpy.data.objects[layer_list[layer_list_active].obj_name]
        node_group = context.space_data.edit_tree
        for node in node_group.nodes:
            node.select = False
            if get_node_type(node) == "BioxelNodes_FetchLayer":
                if node.inputs[0].default_value == layer_obj:
                    node.select = True


class BIOXELNODES_Layer(bpy.types.PropertyGroup):
    obj_name: bpy.props.StringProperty()   # type: ignore
    label: bpy.props.StringProperty()   # type: ignore
    info_text: bpy.props.StringProperty()   # type: ignore


class BIOXELNODES_LayerListUL(bpy.types.PropertyGroup):
    layer_list: bpy.props.CollectionProperty(
        type=BIOXELNODES_Layer)  # type: ignore
    layer_list_active: bpy.props.IntProperty(default=-1,
                                             update=select_layer,
                                             options=set())  # type: ignore
