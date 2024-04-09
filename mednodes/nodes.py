from .custom_nodes import CustomNodes

MENU_ITEMS = [
    {
        'label': 'Present',
        'items': [
            {
                'label': 'Segment',
                'node_type': 'MedNodes_Segment',
                'node_description': '',
                'node_driver': 'value_offset:Offset'
            }
        ]
    },
    {
        'label': 'Segment',
        'items': [
            {
                'label': 'Segment by Level',
                'node_type': 'MedNodes_SegmentByLevel',
                'node_description': '',
                'node_driver': 'value_offset:Offset'
            },
            {
                'label': 'Segment by Range',
                'node_type': 'MedNodes_SegmentByRange',
                'node_description': '',
                'node_driver': 'value_offset:Offset'
            },
            {
                'label': 'Segment by Layers',
                'node_type': 'MedNodes_SegmentsByLayers',
                'node_description': '',
                'node_driver': 'value_offset:Offset'
            }
        ]
    },
    {
        'label': 'Shader',
        'items': [
            {
                'label': 'Segment Shader',
                'node_type': 'MedNodes_SegmentShader',
                'node_description': ''
            }
        ]
    },
        {
        'label': 'Slicer',
        'items': [
            {
                'label': 'LPS Slicer',
                'node_type': 'MedNodes_LPS-Slicer',
                'node_description': '',
                'node_driver': 'origin:Origin'
            },
            {
                'label': 'Axis Slicer',
                'node_type': 'MedNodes_AxisSlicer',
                'node_description': '',
            },
            {
                'label': 'Box Slicer',
                'node_type': 'MedNodes_BoxSlicer',
                'node_description': '',
            }
        ]
    },
]

custom_nodes = CustomNodes(
    menu_items=MENU_ITEMS,
    nodes_file="assets/Nodes.blend",
    root_label='MedNodes'
)
