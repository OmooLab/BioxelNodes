
from pathlib import Path
from .customnodes import CustomNodes
import bpy


def add_driver_to_node_factory(source_prop, target_prop):
    callback_str = f"""
import bpy
from bioxelnodes.utils import add_direct_driver, get_bioxels_obj
bioxels_obj = get_bioxels_obj(bpy.context.active_object)
if bioxels_obj:
    container_obj = bioxels_obj.parent
    add_direct_driver(
        target=node,
        target_prop='{target_prop}',
        source=container_obj,
        source_prop='{source_prop}'
    )
else:
    print('Cannot find any bioxels.')
    """
    return callback_str


def set_prop_to_node_factory(source_prop, target_prop):
    callback_str = f"""
import bpy
from bioxelnodes.utils import get_bioxels_obj
bioxels_obj = get_bioxels_obj(bpy.context.active_object)
if bioxels_obj:
    container_obj = bioxels_obj.parent
    node.inputs.get('{target_prop}').default_value = container_obj.get(
        '{source_prop}')
else:
    print('Cannot find any bioxels.')
    """
    return callback_str


MENU_ITEMS = [
    {
        'label': 'Presets',
        'icon': 'MESH_MONKEY',
        'items': [
            {
                'label': 'Segment',
                'icon': 'BONE_DATA',
                'node_type': 'BioxelNodes_Segment',
                'node_description': '',
                'node_callback': "\n".join([
                    set_prop_to_node_factory("bioxel_size", "Detail Size"),
                    set_prop_to_node_factory("bioxels_offset", "Offset"),
                ])
            }
        #     {
        #         'label': 'Anatomy',
        #         'icon': 'CONSTRAINT_BONE',
        #         'node_type': 'BioxelNodes_Anatomy',
        #         'node_description': '',
        #         'node_callback': "\n".join([
        #             set_prop_to_node_factory("bioxel_size", "Detail Size"),
        #             set_prop_to_node_factory("bioxels_offset", "Offset"),
        #         ])
        #     }
        ]
    },
    {
        'label': 'Segment',
        'icon': 'OUTLINER_DATA_VOLUME',
        'items': [
            {
                'label': 'Segment by Level',
                'icon': 'EMPTY_SINGLE_ARROW',
                'node_type': 'BioxelNodes_SegmentByLevel',
                'node_description': '',
                'node_callback': "\n".join([
                    set_prop_to_node_factory("bioxel_size", "Detail Size"),
                    set_prop_to_node_factory("bioxels_offset", "Offset"),
                ])
            },
            {
                'label': 'Segment by Range',
                'icon': 'IPO_CONSTANT',
                'node_type': 'BioxelNodes_SegmentByRange',
                'node_description': '',
                'node_callback': "\n".join([
                    set_prop_to_node_factory("bioxel_size", "Detail Size"),
                    set_prop_to_node_factory("bioxels_offset", "Offset"),
                ])
            }
            # {
            #     'label': 'Segment by Layers',
            #     'icon': 'ALIGN_JUSTIFY',
            #     'node_type': 'BioxelNodes_SegmentsByLayers',
            #     'node_description': '',
            #     'node_callback': "\n".join([
            #         set_prop_to_node_factory("bioxel_size", "Detail Size"),
            #         set_prop_to_node_factory("bioxels_offset", "Offset"),
            #     ])
            # }
        ]
    },
    {
        'label': 'Shader',
        'icon': 'SHADING_RENDERED',
        'items': [
            {
                'label': 'Segment Shader',
                'icon': 'OUTLINER_OB_VOLUME',
                'node_type': 'BioxelNodes_SegmentShader',
                'node_description': ''
            }
        ]
    }
]

NODE_FILE = "BioxelNodes_4.0"

if bpy.app.version >= (4, 1, 0):
    MENU_ITEMS.append({
        'label': 'Slicer',
        'icon': 'CLIPUV_DEHLT',
        'items': [
            {
                'label': 'RAS Slicer',
                'icon': 'EMPTY_DATA',
                'node_type': 'BioxelNodes_RAS-Slicer',
                'node_description': ''
            },
            {
                'label': 'Axis Slicer',
                'icon': 'OUTLINER_OB_EMPTY',
                'node_type': 'BioxelNodes_AxisSlicer',
                'node_description': '',
            },
            {
                'label': 'Box Slicer',
                'icon': 'MOD_WIREFRAME',
                'node_type': 'BioxelNodes_BoxSlicer',
                'node_description': '',
            }
        ]
    })
    NODE_FILE = "BioxelNodes_4.1"


custom_nodes = CustomNodes(
    menu_items=MENU_ITEMS,
    nodes_file=Path(__file__).parent / f"assets/Nodes/{NODE_FILE}.blend",
    root_label='Bioxel Nodes',
    root_icon="FILE_VOLUME",
)


def register():
    custom_nodes.register()


def unregister():
    custom_nodes.unregister()
