
from pathlib import Path
from .customnodes import CustomNodes

NODE_FILE = "BioxelNodes_4.2"

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
            {
                'label': 'Volume Shader',
                'icon': 'VOLUME_DATA',
                'node_type': 'BioxelNodes_AssignVolumeShader',
                'node_description': ''
            },
            {
                'label': 'Universal Shader',
                'icon': 'MATSHADERBALL',
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
                'node_type': 'BioxelNodes_ColorPresets',
                'node_description': ''
            },
            {
                'label': 'Color Presets MRI',
                'icon': 'COLOR',
                'node_type': 'BioxelNodes_ColorPresets_MRI',
                'node_description': ''
            },
            "separator",
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
                'label': 'Primitive Cutter',
                'icon': 'MOD_LINEART',
                'node_type': 'BioxelNodes_PrimitiveCutter',
                'node_description': ''
            },
            "separator",
            {
                'label': 'Plane Cutter',
                'icon': 'MESH_PLANE',
                'node_type': 'BioxelNodes_PlaneObjectCutter',
                'node_description': ''
            },
            {
                'label': 'Cylinder Cutter',
                'icon': 'MESH_CYLINDER',
                'node_type': 'BioxelNodes_CylinderObjectCutter',
                'node_description': '',
            },
            {
                'label': 'Cube Cutter',
                'icon': 'MESH_CUBE',
                'node_type': 'BioxelNodes_CubeObjectCutter',
                'node_description': '',
            },
            {
                'label': 'Sphere Cutter',
                'icon': 'MESH_UVSPHERE',
                'node_type': 'BioxelNodes_SphereObjectCutter',
                'node_description': '',
            },
            {
                'label': 'Pie Cutter',
                'icon': 'MESH_CONE',
                'node_type': 'BioxelNodes_PieObjectCutter',
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
            },
            "separator",
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
