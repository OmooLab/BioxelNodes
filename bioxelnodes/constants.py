from pathlib import Path

VERSION = (1, 0, 0)
NODE_LIB_FILENAME = "BioxelNodes_v1.0.x"
NODE_LIB_FILEPATH = Path(Path(__file__).parent,
                         f"assets/Nodes/{NODE_LIB_FILENAME}.blend").resolve()

MENU_ITEMS = [
    {
        'label': 'Component',
        'icon': 'OUTLINER_DATA_VOLUME',
        'items': [
            {
                'label': 'Cutout by Threshold',
                'icon': 'EMPTY_SINGLE_ARROW',
                'name': 'CutoutByThreshold',
                'description': ''
            },
            {
                'label': 'Cutout by Range',
                'icon': 'IPO_CONSTANT',
                'name': 'CutoutByRange',
                'description': ''
            },
            {
                'label': 'Cutout by Color',
                'icon': 'COLOR',
                'name': 'CutoutByColor',
                'description': ''
            },
            "separator",
            {
                'label': 'To Surface',
                'icon': 'MESH_DATA',
                'name': 'ToSurface',
                'description': ''
            },
            {
                'label': 'Join Component',
                'icon': 'CONSTRAINT_BONE',
                'name': 'JoinComponent',
                'description': ''
            },
            {
                'label': 'Slice',
                'icon': 'TEXTURE',
                'name': 'Slice',
                'description': ''
            }
        ]
    },
    {
        'label': 'Properties',
        'icon': 'PROPERTIES',
        'items': [
            {
                'label': 'Set Properties',
                'icon': 'PROPERTIES',
                'name': 'SetProperties',
                'description': ''
            },
            "separator",
            {
                'label': 'Set Color',
                'icon': 'IPO_SINE',
                'name': 'SetColor',
                'description': ''
            },
            {
                'label': 'Set Color by Color',
                'icon': 'IPO_QUINT',
                'name': 'SetColorByColor',
                'description': ''
            },
            {
                'label': 'Set Color by Ramp 2',
                'icon': 'IPO_QUAD',
                'name': 'SetColorByRamp2',
                'description': ''
            },
            {
                'label': 'Set Color by Ramp 3',
                'icon': 'IPO_CUBIC',
                'name': 'SetColorByRamp3',
                'description': ''
            },
            {
                'label': 'Set Color by Ramp 4',
                'icon': 'IPO_QUART',
                'name': 'SetColorByRamp4',
                'description': ''
            },
            {
                'label': 'Set Color by Ramp 5',
                'icon': 'IPO_QUINT',
                'name': 'SetColorByRamp5',
                'description': ''
            }
        ]
    },
    {
        'label': 'Surface',
        'icon': 'MESH_DATA',
        'items': [
            {
                'label': 'Membrane Shader',
                'icon': 'NODE_MATERIAL',
                'name': 'AssignMembraneShader',
                'description': ''
            },
            {
                'label': 'Solid Shader',
                'icon': 'SHADING_SOLID',
                'name': 'AssignSolidShader',
                'description': ''
            },
            {
                'label': 'Slime Shader',
                'icon': 'OUTLINER_DATA_META',
                'name': 'AssignSlimeShader',
                'description': ''
            },

        ]
    },
    {
        'label': 'Transform',
        'icon': 'EMPTY_AXIS',
        'items': [
            {
                'label': 'Transform',
                'icon': 'EMPTY_AXIS',
                'name': 'Transform',
                'description': ''
            },
            {
                'label': 'Transform Parent',
                'icon': 'ORIENTATION_PARENT',
                'name': 'TransformParent',
                'description': ''
            },
            {
                'label': 'ReCenter',
                'icon': 'PROP_CON',
                'name': 'ReCenter',
                'description': ''
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
                'name': 'Cut',
                'description': ''
            },
            "separator",
            {
                'label': 'Primitive Cutter',
                'icon': 'MOD_LINEART',
                'name': 'PrimitiveCutter',
                'description': ''
            },
            {
                'label': 'Object Cutter',
                'icon': 'MESH_PLANE',
                'name': 'ObjectCutter',
                'description': ''
            }
        ]
    },
    {
        'label': 'Utils',
        'icon': 'MODIFIER',
        'items': [
            {
                'label': 'Pick Surface',
                'icon': 'OUTLINER_OB_MESH',
                'name': 'PickSurface',
                'description': ''
            },
            {
                'label': 'Pick Volume',
                'icon': 'OUTLINER_OB_VOLUME',
                'name': 'PickVolume',
                'description': ''
            },
            {
                'label': 'Pick Shape Wire',
                'icon': 'FILE_VOLUME',
                'name': 'PickShapeWire',
                'description': ''
            },
            {
                'label': 'Pick Bbox Wire',
                'icon': 'MESH_CUBE',
                'name': 'PickBboxWire',
                'description': ''
            },
            "separator",
            {
                'label': 'Inflate',
                'icon': 'OUTLINER_OB_META',
                'name': 'Inflate',
                'description': ''
            },
            {
                'label': 'Smooth',
                'icon': 'MOD_SMOOTH',
                'name': 'Smooth',
                'description': ''
            },
            {
                'label': 'Remove Small Island',
                'icon': 'FORCE_LENNARDJONES',
                'name': 'RemoveSmallIsland',
                'description': ''
            }
        ]
    }
]
