from pathlib import Path

VERSIONS = [{"label": "Latest", "node_version": (1, 0, 1)},
            {"label": "v0.3.x", "node_version": (0, 3, 3)},
            {"label": "v0.2.x", "node_version": (0, 2, 9)}]

NODE_LIB_DIRPATH = Path(Path(__file__).parent,
                        "assets/Nodes").resolve()

LATEST_NODE_LIB_PATH = lib_path = Path(NODE_LIB_DIRPATH,
                                  "BioxelNodes_latest.blend").resolve()

COMPONENT_OUTPUT_NODES = [
    "CutoutByThreshold",
    "CutoutByRange",
    "CutoutByHue",
    "JoinComponent",
    "SetProperties",
    "SetColor",
    "SetColorByColor",
    "SetColorByColor",
    "SetColorByRamp2",
    "SetColorByRamp3",
    "SetColorByRamp4",
    "SetColorByRamp5",
    "Cut",
]

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
                'label': 'Cutout by Hue',
                'icon': 'COLOR',
                'name': 'CutoutByHue',
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
        'label': 'Property',
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
        'label': 'Cut',
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
        'label': 'Extra',
        'icon': 'MODIFIER',
        'items': [
            {
                'label': 'Fetch Mesh',
                'icon': 'OUTLINER_OB_MESH',
                'name': 'FetchMesh',
                'description': ''
            },
            {
                'label': 'Fetch Volume',
                'icon': 'OUTLINER_OB_VOLUME',
                'name': 'FetchVolume',
                'description': ''
            },
            {
                'label': 'Fetch Shape Wire',
                'icon': 'FILE_VOLUME',
                'name': 'FetchShapeWire',
                'description': ''
            },
            {
                'label': 'Fetch Bbox Wire',
                'icon': 'MESH_CUBE',
                'name': 'FetchBboxWire',
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
