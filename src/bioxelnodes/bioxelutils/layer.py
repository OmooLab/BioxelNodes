import random
import re
import bpy
import numpy as np

import pyopenvdb as vdb
from pathlib import Path
from uuid import uuid4

from ..bioxel.layer import Layer
from ..utils import get_use_link
from .node import add_node_to_graph
from .common import (get_layer_prop_value,
                     move_node_between_nodes)


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
            if grid["layer_kind"] in ['label', 'scalar']:
                data_shape = grid["data_shape"]
            else:
                data_shape = tuple(list(grid["data_shape"]) + [3])
            data_frame = np.ndarray(data_shape, np.float32)
            grid.copyToArray(data_frame)
            data_frames += (data_frame,)
        data = np.stack(data_frames)
    else:
        grids, base_metadata = vdb.readAll(str(cache_filepath))
        grid = grids[0]
        metadata = grid.metadata
        if grid["layer_kind"] in ['label', 'scalar']:
            data_shape = grid["data_shape"]
        else:
            data_shape = tuple(list(grid["data_shape"]) + [3])
        data = np.ndarray(data_shape, np.float32)
        grid.copyToArray(data)
        data = np.expand_dims(data, axis=0)  # expend frame

    name = get_layer_prop_value(layer_obj, "name") \
        or metadata["layer_name"]
    kind = get_layer_prop_value(layer_obj, "kind") \
        or metadata["layer_kind"]
    affine = metadata["layer_affine"]
    dtype = get_layer_prop_value(layer_obj, "dtype") \
        or metadata.get("data_dtype") or "float32"
    offset = get_layer_prop_value(layer_obj, "offset") \
        or metadata.get("data_offset") or 0

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

    layer_display_name = f"{container_obj.name}_{layer.name}"
    if layer.frame_count > 1:
        print(f"Saving the Cache of {layer.name}...")
        vdb_name = str(uuid4())
        sequence_path = Path(cache_dir, vdb_name)
        sequence_path.mkdir(parents=True, exist_ok=True)

        cache_filepaths = []
        for f in range(layer.frame_count):
            if layer.kind in ['label', 'scalar']:
                grid = vdb.FloatGrid()
                grid.copyFromArray(data[f, :, :, :].copy().astype(np.float32))
            else:
                # color
                grid = vdb.Vec3SGrid()
                grid.copyFromArray(
                    data[f, :, :, :, :].copy().astype(np.float32))
            grid.transform = vdb.createLinearTransform(
                layer.affine.transpose())
            grid.metadata = metadata
            grid.name = layer.kind

            cache_filepath = Path(sequence_path,
                                  f"{vdb_name}.{str(f+1).zfill(4)}.vdb")
            vdb.write(str(cache_filepath), grids=[grid])
            cache_filepaths.append(cache_filepath)

    else:
        if layer.kind in ['label', 'scalar']:
            grid = vdb.FloatGrid()
            grid.copyFromArray(data[0, :, :, :].copy().astype(np.float32))
        else:
            # color
            grid = vdb.Vec3SGrid()
            grid.copyFromArray(data[0, :, :, :, :].copy().astype(np.float32))
        grid.transform = vdb.createLinearTransform(
            layer.affine.transpose())
        grid.metadata = metadata
        grid.name = layer.kind

        print(f"Saving the Cache of {layer.name}...")
        cache_filepath = Path(cache_dir, f"{uuid4()}.vdb")
        vdb.write(str(cache_filepath), grids=[grid])
        cache_filepaths = [cache_filepath]

    layer_data = bpy.data.volumes.new(layer_display_name)
    layer_data.render.space = 'WORLD'
    scene_scale = container_obj.get("scene_scale") or 0.01
    step_size = container_obj.get("step_size") or 1
    layer_data.render.step_size = scene_scale * step_size
    layer_data.sequence_mode = 'REPEAT'
    layer_data.filepath = str(cache_filepaths[0])

    if layer.frame_count > 1:
        layer_data.is_sequence = True
        layer_data.frame_duration = layer.frame_count
    else:
        layer_data.is_sequence = False

    layer_obj = bpy.data.objects.new(layer_display_name, layer_data)
    layer_obj['bioxel_layer'] = True

    print(f"Creating Node for {layer.name}...")
    modifier = layer_obj.modifiers.new("GeometryNodes", 'NODES')
    node_group = bpy.data.node_groups.new('GeometryNodes', 'GeometryNodeTree')
    node_group.interface.new_socket(name="Cache",
                                    in_out="INPUT",
                                    socket_type="NodeSocketGeometry")
    node_group.interface.new_socket(name="Layer",
                                    in_out="OUTPUT",
                                    socket_type="NodeSocketGeometry")
    modifier.node_group = node_group

    layer_node = add_node_to_graph("_Layer",
                                   node_group,
                                   use_link=get_use_link())

    layer_node.inputs['name'].default_value = layer.name
    layer_node.inputs['shape'].default_value = layer.shape
    layer_node.inputs['kind'].default_value = layer.kind

    for i in range(layer.affine.shape[1]):
        for j in range(layer.affine.shape[0]):
            affine_key = f"affine{i}{j}"
            layer_node.inputs[affine_key].default_value = layer.affine[j, i]

    layer_node.inputs['unique'].default_value = random.uniform(0, 1)
    layer_node.inputs['bioxel_size'].default_value = layer.bioxel_size[0]
    layer_node.inputs['dtype'].default_value = layer.dtype.str
    layer_node.inputs['dtype_num'].default_value = layer.dtype.num
    layer_node.inputs['frame_count'].default_value = layer.frame_count
    layer_node.inputs['channel_count'].default_value = layer.channel_count
    layer_node.inputs['offset'].default_value = max(0, -layer.min)
    layer_node.inputs['min'].default_value = layer.min
    layer_node.inputs['max'].default_value = layer.max

    input_node = node_group.nodes.new("NodeGroupInput")
    output_node = node_group.nodes.new("NodeGroupOutput")

    node_group.links.new(input_node.outputs[0],
                         layer_node.inputs[0])
    node_group.links.new(layer_node.outputs[0],
                         output_node.inputs[0])

    move_node_between_nodes(
        layer_node, [input_node, output_node])

    layer_obj.parent = container_obj

    return layer_obj
