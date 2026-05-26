from pathlib import Path
from ast import literal_eval

import shutil
import bpy
import numpy as np

from .node import get_nodes_by_type
from .constants import LATEST_NODE_LIB_PATH, NODE_LIB_DIRPATH, PREVIEW_COLLECTIONS


def copy_to_dir(source_path, dir_path, new_name=None, exist_ok=True):
    source = Path(source_path)
    target = Path(dir_path)

    # Check if the source exists
    if not source.exists():
        raise FileNotFoundError

    # Check if the target exists
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)

    target_path = target / new_name if new_name else target / source.name
    # If source is a file, copy it to the target directory
    if source.is_file():
        try:
            shutil.copy(source, target_path)
        except shutil.SameFileError:
            if exist_ok:
                pass
            else:
                raise shutil.SameFileError
    # If source is a directory, copy its contents to the target directory
    elif source.is_dir():
        shutil.copytree(source, target_path, dirs_exist_ok=exist_ok)

    if not target_path.exists():
        raise Exception


def select_object(target_obj):
    for obj in bpy.data.objects:
        obj.select_set(False)

    target_obj.select_set(True)
    bpy.context.view_layer.objects.active = target_obj


def progress_bar(self, context):
    row = self.layout.row()
    row.progress(
        factor=context.window_manager.bioxel_progress_factor,
        type="BAR",
        text=context.window_manager.bioxel_progress_text
    )
    row.scale_x = 2


def progress_update(context, factor, text=""):
    bpy.context.window_manager.bioxel_progress_factor = factor
    bpy.context.window_manager.bioxel_progress_text = text


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


def get_cache_dir():
    preferences = get_preferences()
    cache_path = Path(preferences.cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def get_use_link():
    preferences = get_preferences()
    return preferences.node_import_method == "LINK"


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
    return False


def get_node_lib_path(node_version):
    version_str = "v"+".".join([str(i) for i in list(node_version)])
    lib_filename = f"BioxelNodes_{version_str}.blend"
    return Path(NODE_LIB_DIRPATH,
                lib_filename).resolve()


def local_lib_not_updated():
    return False


def ndarray_to_png(array: np.ndarray, save_path: str):
    """
    Create a PNG from a 2D or 3-channel slice array using Blender API.
    slice_arr expected shape: (W, H) or (W, H, 1) or (W,H,3). Values assumed numeric.

    The function:
    - Converts single-channel arrays to RGB by repeating channel.
    - Flips the image vertically to match Blender's origin.
    - Writes the image file to save_path using a temporary Blender image datablock.

    Parameters:
    - array: numpy ndarray representing the slice (W,H,C) or (W,H,1) or (W,H)
    - save_path: destination PNG filepath
    """
    save_path = Path(save_path)
    h, w = array.shape[0], array.shape[1]
    if array.shape[2] == 1:
        img = np.concatenate([array, array, array], axis=2)
    else:
        img = array[..., :3]

    # Blender expects pixels as sequence of floats in RGBA, length w*h*4
    # NOTE: Blender's image origin is bottom-left; we'll flip vertically for visual consistency.
    img = np.flipud(img)
    pixels = np.empty((h * w * 4,), dtype=np.float32)
    # fill
    pixels[0::4] = img[..., 0].ravel()
    pixels[1::4] = img[..., 1].ravel()
    pixels[2::4] = img[..., 2].ravel()
    pixels[3::4] = 1.0

    # create a temporary image datablock, save then remove
    name = "tmp"
    image = bpy.data.images.new(
        name, width=w, height=h, alpha=True, float_buffer=False)
    image.pixels = pixels.tolist()
    # ensure format and filepath then save
    image.filepath_raw = str(save_path)
    image.file_format = "PNG"
    image.save()
    # remove from data to avoid clutter
    try:
        bpy.data.images.remove(image)
    except Exception:
        pass


def split_text_to_lines(text: str, max_chars: int = 60) -> list:
    """
    Split `text` into multiple lines not exceeding `max_chars` where possible.
    Breaks on whitespace; long words are chunked.
    Returns list of line strings.
    """
    if not text:
        return []
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        if cur:
            candidate = cur + " " + w
        else:
            candidate = w
        if len(candidate) <= max_chars:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            # if single word longer than max_chars, chunk it
            if len(w) > max_chars:
                for i in range(0, len(w), max_chars):
                    lines.append(w[i: i + max_chars])
                cur = ""
            else:
                cur = w
    if cur:
        lines.append(cur)
    return lines


def wrapped_label(layout, text: str, max_chars: int = 42):
    """
    Helper to add multiple layout.label calls for a long text.
    """
    for line in split_text_to_lines(text, max_chars=max_chars):
        layout.label(text=line)


def refresh_bioxel_panels(context):
    """
    Force Bioxel UI to refresh.

    - Tags relevant areas for redraw.
    - Nudges the bioxel_layer_gallery EnumProperty to force items() re-evaluation
      when possible (helps template_icon_view pick up updated icons/paths).
    Use this from operators after they change b i o x e l _ l a y e r s or previews.
    """

    # tag redraw for all windows/areas
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            # target node editor and other UI areas that may show previews
            if area.type in {"NODE_EDITOR", "VIEW_3D", "IMAGE_EDITOR", "OUTLINER"}:
                area.tag_redraw()


def load_icon(filepath: Path, key: str):
    pcoll = PREVIEW_COLLECTIONS["layers"]

    try:
        icon = pcoll[key].icon_id
    except KeyError:
        if filepath.exists():
            pcoll.load(key, str(filepath), "IMAGE")

        try:
            icon = pcoll[key].icon_id
        except KeyError:
            icon = "TEXTURE"

    return icon
