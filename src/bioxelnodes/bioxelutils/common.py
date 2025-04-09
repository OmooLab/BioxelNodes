from ast import literal_eval
from pathlib import Path
import bpy

from ..constants import LATEST_NODE_LIB_PATH, NODE_LIB_DIRPATH, VERSIONS
from ..utils import get_cache_dir


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


def get_container_objs_from_selection():
    container_objs = []
    for obj in bpy.context.selected_objects:
        if get_container_obj(obj):
            container_objs.append(obj)

    return list(set(container_objs))


def get_container_obj(current_obj):
    if current_obj:
        if current_obj.get('bioxel_container'):
            return current_obj
        elif current_obj.get('bioxel_layer'):
            parent = current_obj.parent
            return parent if parent.get('bioxel_container') else None
    return None


def get_layer_prop_value(layer_obj: bpy.types.Object, prop_name: str):
    node_group = layer_obj.modifiers[0].node_group
    layer_node = get_nodes_by_type(node_group, "BioxelNodes__Layer")[0]
    prop = layer_node.inputs.get(prop_name)
    if prop is None:
        return None

    value = prop.default_value

    if type(value).__name__ == "bpy_prop_array":
        value = tuple(value)
        return tuple([int(v) for v in value]) \
            if prop in ["shape"] else value
    elif type(value).__name__ == "str":
        return str(value)
    elif type(value).__name__ == "float":
        value = float(value)
        return round(value, 2) \
            if prop in ["bioxel_size"] else value
    elif type(value).__name__ == "int":
        value = int(value)
        return value
    else:
        return value


def get_layer_name(layer_obj):
    return get_layer_prop_value(layer_obj, "name")


def get_layer_kind(layer_obj):
    return get_layer_prop_value(layer_obj, "kind")


def get_layer_label(layer_obj):
    name = get_layer_name(layer_obj)
    # kind = get_layer_kind(layer_obj)

    label = f"{name}"

    if is_missing_layer(layer_obj):
        return "**MISSING**" + label
    elif is_temp_layer(layer_obj):
        return "* " + label
    else:
        return label


def is_missing_layer(layer_obj):
    cache_filepath = Path(bpy.path.abspath(
        layer_obj.data.filepath)).resolve()
    return not cache_filepath.is_file()


def is_temp_layer(layer_obj):
    cache_filepath = Path(bpy.path.abspath(
        layer_obj.data.filepath)).resolve()
    cache_dirpath = Path(get_cache_dir())
    return cache_dirpath in cache_filepath.parents


def set_layer_prop_value(layer_obj: bpy.types.Object, prop: str, value):
    node_group = layer_obj.modifiers[0].node_group
    layer_node = get_nodes_by_type(node_group, "BioxelNodes__Layer")[0]
    layer_node.inputs[prop].default_value = value


def get_layer_obj(current_obj: bpy.types.Object):
    if current_obj:
        if current_obj.get('bioxel_layer') and current_obj.parent:
            if current_obj.parent.get('bioxel_container'):
                return current_obj
    return None


def get_container_layer_objs(container_obj: bpy.types.Object):
    layer_objs = []
    for obj in bpy.data.objects:
        if obj.parent == container_obj and get_layer_obj(obj):
            layer_objs.append(obj)

    return layer_objs


def get_all_layer_objs():
    layer_objs = []
    for obj in bpy.data.objects:
        if get_layer_obj(obj):
            layer_objs.append(obj)

    return layer_objs


def add_driver(target, target_prop, var_sources, expression):
    driver = target.driver_add(target_prop)
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
    drivers = [
        {
            "source": source,
            "prop": source_prop
        }
    ]
    expression = "var0"
    add_driver(target, target_prop, drivers, expression)


def read_file_prop(content: str):
    props = {}
    for line in content.split("\n"):
        line = line.replace(" ", "")
        p = line.split("=")[0]
        if p != "":
            v = line.split("=")[-1]
            props[p] = v
    return props


def write_file_prop(props: dict):
    lines = []
    for p, v in props.items():
        lines.append(f"{p} = {v}")
    return "\n".join(lines)


def set_file_prop(prop, value):
    if bpy.data.texts.get("BioxelNodes") is None:
        bpy.data.texts.new("BioxelNodes")

    props = read_file_prop(bpy.data.texts["BioxelNodes"].as_string())
    props[prop] = value
    bpy.data.texts["BioxelNodes"].clear()
    bpy.data.texts["BioxelNodes"].write(write_file_prop(props))


def get_file_prop(prop):
    if bpy.data.texts.get("BioxelNodes") is None:
        bpy.data.texts.new("BioxelNodes")

    props = read_file_prop(bpy.data.texts["BioxelNodes"].as_string())
    return props.get(prop)


def get_node_version():
    node_version = get_file_prop("node_version")
    return literal_eval(node_version) if node_version else None


def is_incompatible():
    node_version = get_node_version()
    if node_version is None:
        for node_group in bpy.data.node_groups:
            if node_group.name.startswith("BioxelNodes"):
                return True
    else:
        addon_version = VERSIONS[0]["node_version"]
        if node_version[0] != addon_version[0]\
                or node_version[1] != addon_version[1]:
            return True

    return False


def get_node_lib_path(node_version):
    version_str = "v"+".".join([str(i) for i in list(node_version)])
    lib_filename = f"BioxelNodes_{version_str}.blend"
    return Path(NODE_LIB_DIRPATH,
                lib_filename).resolve()


def local_lib_not_updated():
    addon_version = VERSIONS[0]["node_version"]
    addon_lib_path = LATEST_NODE_LIB_PATH

    use_local = False
    for node_group in bpy.data.node_groups:
        if node_group.name.startswith("BioxelNodes"):
            lib = node_group.library
            if lib:
                lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()
                if lib_path != addon_lib_path:
                    use_local = True
                    break

    not_update = get_node_version() != addon_version
    return use_local and not_update


def get_output_node(node_group):
    try:
        output_node = get_nodes_by_type(node_group,
                                        'NodeGroupOutput')[0]
    except:
        output_node = node_group.nodes.new("NodeGroupOutput")

    return output_node
