import random
import re
import bpy
import numpy as np

import pyopenvdb as vdb
from pathlib import Path
from uuid import uuid4

from ..nodes import custom_nodes
from ..bioxel.layer import Layer
from .node import get_nodes_by_type, move_node_between_nodes


def get_layer_obj(current_obj: bpy.types.Object):
    if current_obj:
        if current_obj.get('bioxel_layer') and current_obj.parent:
            if current_obj.parent.get('bioxel_container'):
                return current_obj
    return None


def get_container_layer_objs(container_obj: bpy.types.Object):
    layer_objs = []
    for obj in bpy.context.scene.objects:
        if obj.parent == container_obj and get_layer_obj(obj):
            layer_objs.append(obj)

    return layer_objs


def get_all_layer_objs():
    layer_objs = []
    for obj in bpy.context.scene.objects:
        if get_layer_obj(obj):
            layer_objs.append(obj)

    return layer_objs


def obj_to_layer(layer_obj: bpy.types.Object):
    cache_filepath = Path(bpy.path.abspath(layer_obj.data.filepath)).resolve()
    is_sequence = re.search(r'\.\d{4}\.',
                            cache_filepath.name) is not None
    if is_sequence:
        cache_path = cache_filepath.parent
        data_frames = ()
        for f in cache_path.iterdir():
            if not f.is_file() or f.suffix != ".vdb":
                continue
            grids, base_metadata = vdb.readAll(str(f))
            grid = grids[0]
            metadata = grid.metadata
            data_frame = np.ndarray(grid["data_shape"], np.float32)
            grid.copyToArray(data_frame)
            data_frames += (data_frame,)
        data = np.stack(data_frames)
    else:
        grids, base_metadata = vdb.readAll(str(cache_filepath))
        grid = grids[0]
        metadata = grid.metadata
        data = np.ndarray(grid["data_shape"], np.float32)
        grid.copyToArray(data)
        data = np.expand_dims(data, axis=0)  # expend frame

    name = metadata["layer_name"]
    kind = metadata["layer_kind"]
    affine = metadata["layer_affine"]
    dtype = metadata.get("data_dtype") or "float32"
    offset = metadata.get("data_offset") or 0
    data = data - np.full_like(data, offset)
    data = data.astype(dtype)

    if kind in ["scalar", "label"]:
        data = np.expand_dims(data, axis=-1)  # expend channel

    layer = Layer(data=data,
                  name=name,
                  kind=kind,
                  affine=affine)

    return layer


def layer_to_obj(layer: Layer,
                 container_obj: bpy.types.Object,
                 cache_dir: str):

    data = layer.data

    # TXYZC > TXYZ
    if layer.kind in ['label', 'scalar']:
        data = np.amax(data, -1)

    offset = 0
    if layer.kind in ['scalar']:
        data = data.astype(np.float32)
        orig_min = float(np.min(data))
        if orig_min < 0:
            offset = -orig_min

        data = data + np.full_like(data, offset)

    metadata = {
        "layer_name": layer.name,
        "layer_kind": layer.kind,
        "layer_affine": layer.affine.tolist(),
        "data_shape": layer.shape,
        "data_dtype": layer.data.dtype.str,
        "data_offset": offset
    }

    if layer.frame_count > 1:
        print(f"Saving the Cache of {layer.name}...")
        vdb_name = str(uuid4())
        sequence_path = Path(cache_dir, vdb_name)
        sequence_path.mkdir(parents=True, exist_ok=True)

        cache_filepaths = []
        for f in range(layer.frame_count):
            grid = vdb.FloatGrid()
            grid.copyFromArray(data[f, :, :, :].copy().astype(np.float32))
            grid.transform = vdb.createLinearTransform(
                layer.affine.transpose())
            grid.metadata = metadata
            grid.name = layer.kind

            cache_filepath = Path(sequence_path,
                                  f"{vdb_name}.{str(f+1).zfill(4)}.vdb")
            vdb.write(str(cache_filepath), grids=[grid])
            cache_filepaths.append(cache_filepath)

        print(f"Loading the Cache of {layer.name}...")
        files = [{"name": str(cache_filepath.name), "name": str(cache_filepath.name)}
                 for cache_filepath in cache_filepaths]

        bpy.ops.object.volume_import(filepath=str(cache_filepaths[0]),
                                     directory=str(cache_filepaths[0].parent),
                                     files=files, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

    else:
        grid = vdb.FloatGrid()
        grid.copyFromArray(data[0, :, :, :].copy().astype(np.float32))
        grid.transform = vdb.createLinearTransform(
            layer.affine.transpose())
        grid.metadata = metadata
        grid.name = layer.kind

        print(f"Saving the Cache of {layer.name}...")
        cache_filepath = Path(cache_dir, f"{uuid4()}.vdb")
        vdb.write(str(cache_filepath), grids=[grid])
        cache_filepaths = [cache_filepath]

        print(f"Loading the Cache of {layer.name}...")
        bpy.ops.object.volume_import(filepath=str(cache_filepaths[0]),
                                     align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

    layer_obj = bpy.context.active_object
    layer_obj.data.sequence_mode = 'REPEAT'

    # Set props to VDB object
    layer_obj.name = f"{container_obj.name}_{layer.name}"
    layer_obj.data.name = f"{container_obj.name}_{layer.name}"

    layer_obj.lock_location[0] = True
    layer_obj.lock_location[1] = True
    layer_obj.lock_location[2] = True
    layer_obj.lock_rotation[0] = True
    layer_obj.lock_rotation[1] = True
    layer_obj.lock_rotation[2] = True
    layer_obj.lock_scale[0] = True
    layer_obj.lock_scale[1] = True
    layer_obj.lock_scale[2] = True

    layer_obj.visible_camera = False
    layer_obj.visible_diffuse = False
    layer_obj.visible_glossy = False
    layer_obj.visible_transmission = False
    layer_obj.visible_volume_scatter = False
    layer_obj.visible_shadow = False

    layer_obj.hide_select = True
    layer_obj.hide_render = True
    layer_obj.hide_viewport = True

    layer_obj['bioxel_layer'] = True
    layer_obj.parent = container_obj

    for collection in layer_obj.users_collection:
        collection.objects.unlink(layer_obj)

    for collection in container_obj.users_collection:
        collection.objects.link(layer_obj)

    print(f"Creating Node for {layer.name}...")
    bpy.ops.node.new_geometry_nodes_modifier()
    node_group = layer_obj.modifiers[0].node_group
    layer_node = custom_nodes.add_node(node_group,
                                          "BioxelNodes__Layer")

    layer_node.inputs['name'].default_value = layer.name
    layer_node.inputs['shape'].default_value = layer.shape
    layer_node.inputs['kind'].default_value = layer.kind

    for i in range(layer.affine.shape[1]):
        for j in range(layer.affine.shape[0]):
            affine_key = f"affine{i}{j}"
            layer_node.inputs[affine_key].default_value = layer.affine[j, i]

    layer_node.inputs['id'].default_value = random.randint(-200000000,
                                                              200000000)
    layer_node.inputs['bioxel_size'].default_value = layer.bioxel_size[0]
    layer_node.inputs['dtype'].default_value = layer.dtype.str
    layer_node.inputs['dtype_num'].default_value = layer.dtype.num
    layer_node.inputs['offset'].default_value = max(0, -layer.min)
    layer_node.inputs['min'].default_value = layer.min
    layer_node.inputs['max'].default_value = layer.max

    input_node = get_nodes_by_type(node_group,
                                   'NodeGroupInput')[0]
    output_node = get_nodes_by_type(node_group,
                                    'NodeGroupOutput')[0]

    node_group.links.new(input_node.outputs[0],
                         layer_node.inputs[0])
    node_group.links.new(layer_node.outputs[0],
                         output_node.inputs[0])

    move_node_between_nodes(
        layer_node, [input_node, output_node])

    return layer_obj
