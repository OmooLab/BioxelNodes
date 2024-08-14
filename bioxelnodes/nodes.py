
from pathlib import Path
from .customnodes import CustomNodes

NODE_FILE = "BioxelNodes_4.2"

MENU_ITEMS = [
    {
        'label': 'Component',
        'icon': 'OUTLINER_DATA_VOLUME',
        'items': [
            {
                'label': 'Cutout by Threshold',
                'icon': 'EMPTY_SINGLE_ARROW',
                'node_type': 'BioxelNodes_CutoutByThreshold',
                'node_description': ''
            },
            {
                'label': 'Cutout by Range',
                'icon': 'IPO_CONSTANT',
                'node_type': 'BioxelNodes_CutoutByRange',
                'node_description': ''
            },
            {
                'label': 'Cutout by Color',
                'icon': 'COLOR',
                'node_type': 'BioxelNodes_CutoutByColor',
                'node_description': ''
            },
            "separator",
            {
                'label': 'To Surface',
                'icon': 'MESH_DATA',
                'node_type': 'BioxelNodes_ToSurface',
                'node_description': ''
            },
            {
                'label': 'Join Component',
                'icon': 'CONSTRAINT_BONE',
                'node_type': 'BioxelNodes_JoinComponent',
                'node_description': ''
            },
        ]
    },
    {
        'label': 'Properties',
        'icon': 'PROPERTIES',
        'items': [
            {
                'label': 'Set Properties',
                'icon': 'PROPERTIES',
                'node_type': 'BioxelNodes_SetProperties',
                'node_description': ''
            },
            "separator",
            {
                'label': 'Set Color',
                'icon': 'IPO_SINE',
                'node_type': 'BioxelNodes_SetColor',
                'node_description': ''
            },
            {
                'label': 'Set Color by Layer',
                'icon': 'IPO_QUINT',
                'node_type': 'BioxelNodes_SetColorByLayer',
                'node_description': ''
            },
            {
                'label': 'Set Color by Ramp 2',
                'icon': 'IPO_QUAD',
                'node_type': 'BioxelNodes_SetColorByRamp2',
                'node_description': ''
            },
            {
                'label': 'Set Color by Ramp 3',
                'icon': 'IPO_CUBIC',
                'node_type': 'BioxelNodes_SetColorByRamp3',
                'node_description': ''
            },
            {
                'label': 'Set Color by Ramp 4',
                'icon': 'IPO_QUART',
                'node_type': 'BioxelNodes_SetColorByRamp4',
                'node_description': ''
            },
            {
                'label': 'Set Color by Ramp 5',
                'icon': 'IPO_QUINT',
                'node_type': 'BioxelNodes_SetColorByRamp5',
                'node_description': ''
            },
            # "separator",
            # {
            #     'label': 'Color Presets',
            #     'icon': 'COLOR',
            #     'node_type': 'BioxelNodes_ColorPresets',
            #     'node_description': ''
            # }
            # {
            #     'label': 'Color Presets MRI',
            #     'icon': 'COLOR',
            #     'node_type': 'BioxelNodes_ColorPresets_MRI',
            #     'node_description': ''
            # },
        ]
    },
    {
        'label': 'Surface',
        'icon': 'MESH_DATA',
        'items': [
            {
                'label': 'Membrane Shader',
                'icon': 'NODE_MATERIAL',
                'node_type': 'BioxelNodes_AssignMembraneShader',
                'node_description': ''
            },
            {
                'label': 'Solid Shader',
                'icon': 'SHADING_SOLID',
                'node_type': 'BioxelNodes_AssignSolidShader',
                'node_description': ''
            },
            {
                'label': 'Slime Shader',
                'icon': 'OUTLINER_DATA_META',
                'node_type': 'BioxelNodes_AssignSlimeShader',
                'node_description': ''
            },
            "separator",
            {
                'label': 'Inflate',
                'icon': 'OUTLINER_OB_META',
                'node_type': 'BioxelNodes_M_Inflate',
                'node_description': ''
            },
            {
                'label': 'Smooth',
                'icon': 'MOD_SMOOTH',
                'node_type': 'BioxelNodes_M_Smooth',
                'node_description': ''
            },
            {
                'label': 'Remove Small Island',
                'icon': 'FORCE_LENNARDJONES',
                'node_type': 'BioxelNodes_M_RemoveSmallIsland',
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
                'label': 'Primitive Cutter',
                'icon': 'MOD_LINEART',
                'node_type': 'BioxelNodes_PrimitiveCutter',
                'node_description': ''
            },
            {
                'label': 'Object Cutter',
                'icon': 'MESH_PLANE',
                'node_type': 'BioxelNodes_ObjectCutter',
                'node_description': ''
            }
        ]
    },
    {
        'label': 'Utils',
        'icon': 'MODIFIER',
        'items': [
            {
                'label': 'Pick Mesh',
                'icon': 'OUTLINER_OB_MESH',
                'node_type': 'BioxelNodes_PickMesh',
                'node_description': ''
            },
            {
                'label': 'Pick Volume',
                'icon': 'OUTLINER_OB_VOLUME',
                'node_type': 'BioxelNodes_PickVolume',
                'node_description': ''
            },
            {
                'label': 'Pick Bbox Wire',
                'icon': 'MESH_CUBE',
                'node_type': 'BioxelNodes_PickBboxWire',
                'node_description': ''
            }
            
        ]
    }
]


custom_nodes = CustomNodes(
    menu_items=MENU_ITEMS,
    nodes_file=Path(__file__).parent / f"assets/Nodes/{NODE_FILE}.blend",
    class_prefix="BIOXELNODES_MT_NODES",
    root_label='Bioxel Nodes',
    root_icon="FILE_VOLUME",
)


def register():
    custom_nodes.register()


def unregister():
    custom_nodes.unregister()
