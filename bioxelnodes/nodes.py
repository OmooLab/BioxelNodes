
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


if bpy.app.version >= (4, 1, 0):
    NODE_FILE = "BioxelNodes_4.1"

    MENU_ITEMS = [
        {
            'label': 'Methods',
            'icon': 'OUTLINER_DATA_VOLUME',
            'items': [
                {
                    'label': 'Mask by Threshold',
                    'icon': 'EMPTY_SINGLE_ARROW',
                    'node_type': 'BioxelNodes_MaskByThreshold',
                    'node_description': ''
                },
                {
                    'label': 'Mask by Range',
                    'icon': 'IPO_CONSTANT',
                    'node_type': 'BioxelNodes_MaskByRange',
                    'node_description': ''
                },
                {
                    'label': 'Mask by Label',
                    'icon': 'MESH_CAPSULE',
                    'node_type': 'BioxelNodes_MaskByLabel',
                    'node_description': ''
                }
            ]
        },
        {
            'label': 'Shaders',
            'icon': 'SHADING_RENDERED',
            'items': [
                {
                    'label': 'Solid Shader',
                    'icon': 'SHADING_SOLID',
                    'node_type': 'BioxelNodes_AssignSolidShader',
                    'node_description': ''
                },
                {
                    'label': 'Slime Shader',
                    'icon': 'OUTLINER_OB_META',
                    'node_type': 'BioxelNodes_AssignSlimeShader',
                    'node_description': ''
                },
                {
                    'label': 'Volume Shader',
                    'icon': 'OUTLINER_OB_VOLUME',
                    'node_type': 'BioxelNodes_AssignVolumeShader',
                    'node_description': ''
                },
                {
                    'label': 'Universal Shader',
                    'icon': 'SHADING_RENDERED',
                    'node_type': 'BioxelNodes_AssignUniversalShader',
                    'node_description': ''
                }
            ]
        },
        {
            'label': 'Colors',
            'icon': 'COLOR',
            'items': [
                {
                    'label': 'Color Presets',
                    'icon': 'COLOR',
                    'node_type': 'BioxelNodes_SetColorPresets',
                    'node_description': ''
                },
                {
                    'label': 'Color Ramp 2',
                    'icon': 'IPO_QUAD',
                    'node_type': 'BioxelNodes_SetColorRamp2',
                    'node_description': ''
                },
                {
                    'label': 'Color Ramp 3',
                    'icon': 'IPO_CUBIC',
                    'node_type': 'BioxelNodes_SetColorRamp3',
                    'node_description': ''
                },
                {
                    'label': 'Color Ramp 4',
                    'icon': 'IPO_QUART',
                    'node_type': 'BioxelNodes_SetColorRamp4',
                    'node_description': ''
                },
                {
                    'label': 'Color Ramp 5',
                    'icon': 'IPO_QUINT',
                    'node_type': 'BioxelNodes_SetColorRamp5',
                    'node_description': ''
                }
            ]
        },
        {
            'label': 'Cutters',
            'icon': 'MOD_BEVEL',
            'items': [
                {
                    'label': 'Cut',
                    'icon': 'MOD_BEVEL',
                    'node_type': 'BioxelNodes_Cut',
                    'node_description': ''
                },
                "separator",
                {
                    'label': 'Plane Cutter',
                    'icon': 'MOD_LATTICE',
                    'node_type': 'BioxelNodes_PlaneCutter',
                    'node_description': '',
                },
                {
                    'label': 'Plane Object Cutter',
                    'icon': 'OUTLINER_OB_LATTICE',
                    'node_type': 'BioxelNodes_PlaneObjectCutter',
                    'node_description': '',
                }
            ]
        },
        {
            'label': 'Utils',
            'icon': 'MODIFIER',
            'items': [
                {
                    'label': 'Join Component',
                    'icon': 'CONSTRAINT_BONE',
                    'node_type': 'BioxelNodes_JoinComponent',
                    'node_description': ''
                }
            ]
        }
    ]

else:
    NODE_FILE = "BioxelNodes_4.0"
    MENU_ITEMS = [
        {
            'label': 'Methods',
            'icon': 'OUTLINER_DATA_VOLUME',
            'items': [
                {
                    'label': 'Mask by Threshold',
                    'icon': 'EMPTY_SINGLE_ARROW',
                    'node_type': 'BioxelNodes_MaskByThreshold',
                    'node_description': ''
                },
                {
                    'label': 'Mask by Range',
                    'icon': 'IPO_CONSTANT',
                    'node_type': 'BioxelNodes_MaskByRange',
                    'node_description': ''
                },
                {
                    'label': 'Mask by Label',
                    'icon': 'MESH_CAPSULE',
                    'node_type': 'BioxelNodes_MaskByLabel',
                    'node_description': ''
                }
            ]
        },
        {
            'label': 'Shaders',
            'icon': 'SHADING_RENDERED',
            'items': [
                {
                    'label': 'Solid Shader',
                    'icon': 'SHADING_SOLID',
                    'node_type': 'BioxelNodes_AssignSolidShader',
                    'node_description': ''
                },
                {
                    'label': 'Slime Shader',
                    'icon': 'OUTLINER_OB_META',
                    'node_type': 'BioxelNodes_AssignSlimeShader',
                    'node_description': ''
                },
                {
                    'label': 'Volume Shader',
                    'icon': 'OUTLINER_OB_VOLUME',
                    'node_type': 'BioxelNodes_AssignVolumeShader',
                    'node_description': ''
                },
                {
                    'label': 'Universal Shader',
                    'icon': 'SHADING_RENDERED',
                    'node_type': 'BioxelNodes_AssignUniversalShader',
                    'node_description': ''
                }
            ]
        },
        {
            'label': 'Colors',
            'icon': 'COLOR',
            'items': [
                {
                    'label': 'Color Ramp 2',
                    'icon': 'IPO_QUAD',
                    'node_type': 'BioxelNodes_SetColorRamp2',
                    'node_description': ''
                },
                {
                    'label': 'Color Ramp 3',
                    'icon': 'IPO_CUBIC',
                    'node_type': 'BioxelNodes_SetColorRamp3',
                    'node_description': ''
                },
                {
                    'label': 'Color Ramp 4',
                    'icon': 'IPO_QUART',
                    'node_type': 'BioxelNodes_SetColorRamp4',
                    'node_description': ''
                },
                {
                    'label': 'Color Ramp 5',
                    'icon': 'IPO_QUINT',
                    'node_type': 'BioxelNodes_SetColorRamp5',
                    'node_description': ''
                }
            ]
        },
        {
            'label': 'Cutters',
            'icon': 'MOD_BEVEL',
            'items': [
                {
                    'label': 'Cut',
                    'icon': 'MOD_BEVEL',
                    'node_type': 'BioxelNodes_Cut',
                    'node_description': ''
                },
                "separator",
                {
                    'label': 'Plane Cutter',
                    'icon': 'MOD_LATTICE',
                    'node_type': 'BioxelNodes_PlaneCutter',
                    'node_description': '',
                },
                {
                    'label': 'Plane Object Cutter',
                    'icon': 'OUTLINER_OB_LATTICE',
                    'node_type': 'BioxelNodes_PlaneObjectCutter',
                    'node_description': '',
                }
            ]
        },
        {
            'label': 'Utils',
            'icon': 'MODIFIER',
            'items': [
                {
                    'label': 'Join Component',
                    'icon': 'CONSTRAINT_BONE',
                    'node_type': 'BioxelNodes_JoinComponent',
                    'node_description': ''
                }
            ]
        }
    ]


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
