import bpy
import mathutils
from pathlib import Path
import pyopenvdb as vdb
from uuid import uuid4


def move_node_to_node(node, target_node, offset=(0, 0)):
    node.location.x = target_node.location.x + offset[0]
    node.location.y = target_node.location.y + offset[1]


def move_node_between_nodes(node, target_nodes, offset=(0, 0)):
    xs = []
    ys = []
    for target_node in target_nodes:
        xs.append(target_node.location.x)
        ys.append(target_node.location.y)

    node.location.x = sum(xs) / len(xs) + offset[0]
    node.location.y = sum(ys) / len(ys) + offset[1]


def get_node_type(node):
    node_type = type(node).__name__
    if node_type == "GeometryNodeGroup":
        node_type = node.node_tree.name

    return node_type


def get_nodes_by_type(node_group, type_name: str):
    return [node for node in node_group.nodes if get_node_type(node) == type_name]


def show_message(message="", title="Message Box", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def calc_bbox_verts(origin, size):
    bbox_origin = mathutils.Vector(
        (origin[0], origin[1], origin[2]))
    bbox_size = mathutils.Vector(
        (size[0], size[1], size[2]))
    bbox_verts = [
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + 0,
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + 0,
            bbox_origin[2] + bbox_size[2]
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + bbox_size[2]
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + 0,
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + 0,
            bbox_origin[2] + bbox_size[2],
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + 0,
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + bbox_size[2],
        ),
    ]
    return bbox_verts


def lock_transform(obj):
    obj.lock_location[0] = True
    obj.lock_location[1] = True
    obj.lock_location[2] = True
    obj.lock_rotation[0] = True
    obj.lock_rotation[1] = True
    obj.lock_rotation[2] = True
    obj.lock_scale[0] = True
    obj.lock_scale[1] = True
    obj.lock_scale[2] = True


def hide_in_ray(obj):
    obj.visible_camera = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False
    obj.visible_volume_scatter = False
    obj.visible_shadow = False


def save_vdb(grids, context):
    preferences = context.preferences.addons[__package__].preferences
    cache_dir = Path(preferences.cache_dir, 'VDBs')
    cache_dir.mkdir(parents=True, exist_ok=True)

    vdb_path = Path(cache_dir, f"{uuid4()}.vdb")
    print(f"Storing the VDB file ({str(vdb_path)})...")
    vdb.write(str(vdb_path), grids=grids)

    return vdb_path


def get_container_from_selection():
    containers = []
    for obj in bpy.context.selected_objects:
        if get_container(obj):
            containers.append(obj)

    return containers


def get_container(current_obj):
    if current_obj:
        if current_obj.get('bioxel_container'):
            return current_obj
        elif current_obj.get('bioxel_layer'):
            parent = current_obj.parent
            return parent if parent.get('bioxel_container') else None
    return None


def get_layer(current_obj):
    if current_obj:
        if current_obj.get('bioxel_layer') and current_obj.parent:
            if current_obj.parent.get('bioxel_container'):
                return current_obj
    return None


def get_container_layers(container):
    layers = []
    for obj in bpy.data.objects:
        if obj.parent == container and get_layer(obj):
            layers.append(obj)

    return layers


def get_all_layers():
    layers = []
    for obj in bpy.data.objects:
        if get_layer(obj):
            layers.append(obj)

    return layers


def get_text_index_str(text):
    # Initialize an empty string to store the digits
    digits = ""

    # Iterate through the characters in reverse order
    started = False
    for char in text[::-1]:
        if char.isdigit():
            started = True
            # If the character is a digit, add it to the digits string
            digits += char
        else:
            if started:
                # If a non-digit character is encountered, stop the loop
                break

    # Reverse the digits string to get the correct order
    last_number = digits[::-1]

    return last_number


def add_driver(target_prop, var_sources, expression):

    driver = target_prop.driver_add("default_value")
    is_vector = isinstance(driver, list)
    drivers = driver if is_vector else [driver]

    for i, driver in enumerate(drivers):
        for j, var_source in enumerate(var_sources):

            source = var_source['source']
            prop = var_source['prop']

            var = driver.driver.variables.new()
            var.name = f"var{j}"

            var.targets[0].id_type = source.id_type
            var.targets[0].id = source
            var.targets[0].data_path = f'["{prop}"][{i}]'\
                if is_vector else f'["{prop}"]'

        driver.driver.expression = expression


def add_direct_driver(target, target_prop, source, source_prop):
    target_prop = target.inputs.get(target_prop)
    drivers = [
        {
            "source": source,
            "prop": source_prop
        }
    ]
    expression = "var0"
    add_driver(target_prop, drivers, expression)
