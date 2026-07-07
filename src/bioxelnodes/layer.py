import json
import time
from typing import Any, List, Dict
from pathlib import Path
import matplotlib.pyplot as plt

import bpy
import numpy as np

try:
    import openvdb as vdb
except ImportError:
    vdb = None

from .bioxel.layer import Layer
from .utils import ndarray_to_png

LAYERS_JSON = "bioxel_layers"


def cache_layer_data(layer: Layer, cache_path: str):
    """
    Cache the given Layer's data as one or more VDB files.

    - For multi-frame layers, writes per-frame VDB files named data.0001.vdb, data.0002.vdb, ...
    - For single-frame layers, writes a single data.vdb file.
    - Applies basic type handling:
      - label/scalar layers collapse channel dimension via max.
      - scalar layers are offset to avoid negative values.
    - The VDB grids will have their transform set from layer.affine but no additional metadata is written.

    Parameters:
    - layer: Layer object containing ndarray data and metadata.
    - cache_path: directory path where VDB files will be written (created if missing).
    """
    data = layer.data

    # 处理标量/标签类型（去除通道维度）
    if layer.kind in ["label", "scalar"]:
        data = np.amax(data, -1)

    # 标量类型偏移处理（避免负值）
    offset = 0
    if layer.kind in ["scalar"]:
        data = data.astype(np.float32)
        orig_min = float(np.min(data))
        if orig_min < 0:
            offset = -orig_min
        data = data + np.full_like(data, offset)

    # 创建缓存目录
    cache_path = Path(cache_path)
    cache_path.mkdir(parents=True, exist_ok=True)

    # 多帧序列处理
    if layer.frame_count > 1:
        for f in range(layer.frame_count):
            # 根据图层类型创建VDB网格
            if layer.kind in ["label", "scalar"]:
                grid = vdb.FloatGrid()
                grid.copyFromArray(data[f, :, :, :].copy().astype(np.float32))
            else:  # 颜色类型
                grid = vdb.Vec3SGrid()
                grid.copyFromArray(data[f, :, :, :, :].copy().astype(np.float32))

            # 仅设置transform，不存储metadata
            grid.transform = vdb.createLinearTransform(layer.affine.transpose())
            grid.name = layer.kind

            # 保存序列帧VDB
            data_filepath = cache_path / f"data.{str(f+1).zfill(4)}.vdb"
            vdb.write(str(data_filepath), grids=[grid])

    else:
        # 单帧处理
        if layer.kind in ["label", "scalar"]:
            grid = vdb.FloatGrid()
            grid.copyFromArray(data[0, :, :, :].copy().astype(np.float32))
        else:  # 颜色类型
            grid = vdb.Vec3SGrid()
            grid.copyFromArray(data[0, :, :, :, :].copy().astype(np.float32))

        # 仅设置transform，不存储metadata
        grid.transform = vdb.createLinearTransform(layer.affine.transpose())
        grid.name = layer.kind

        # 保存单帧VDB
        data_filepath = cache_path / "data.vdb"
        vdb.write(str(data_filepath), grids=[grid])


def cache_layer_snapshot(layer: Layer, cache_path: str):
    """
    Create and save a low-resolution snapshot (numpy .npy) of the layer and generate PNG slices.

    - Saves a 3D numpy ndarray snapshot to <cache_path>/snapshot.npy.
    - Then creates per-Z PNGs in the same directory via snapshot_to_pngs.

    Parameters:
    - layer: Layer to snapshot (expects Layer.snapshot method).
    - cache_path: destination directory where snapshot.npy and PNGs will be created.
    """
    cache_path = Path(cache_path)
    cache_path.mkdir(parents=True, exist_ok=True)

    snapshot_filepath = cache_path / "snapshot.npy"
    snapshot = layer.snapshot((64, 64, 32))
    np.save(str(snapshot_filepath), snapshot)
    snapshot_to_pngs(
        snapshot, str(cache_path), normalize=layer.kind in ["scalar", "vector"]
    )

    if layer.kind in ["scalar", "vector", "color"]:
        plt.figure(figsize=(8, 8))

        def plot_histogram(plt, data, color="black"):
            flattened = data.flatten()
            x_min = np.percentile(flattened, 1)
            x_max = np.percentile(flattened, 99)

            n, bins, _ = plt.hist(
                flattened,
                bins=50,  # 自动根据数据密度调整bins数量（避免空柱）
                range=(x_min, x_max),  # 只显示核心区域，省略稀疏部分
                alpha=0,
                edgecolor="none",  # 去除边框，使柱形更紧凑
            )
            bin_centers = 0.5 * (bins[1:] + bins[:-1])  # 计算每个bin的中点
            plt.plot(bin_centers, n, color=color, linewidth=4)  # 折线
            plt.fill_between(bin_centers, n, color=color, alpha=0.1)

        if layer.kind == "scalar":
            plot_histogram(plt, layer.data[:, :, :, 0], color="black")
        elif layer.kind in ["vector", "color"]:
            plot_histogram(plt, layer.data[:, :, :, 0], color="tomato")
            plot_histogram(plt, layer.data[:, :, :, 1], color="yellowgreen")
            plot_histogram(plt, layer.data[:, :, :, 2], color="xkcd:azure")

        plt.yscale("log")
        plt.gca().get_yaxis().set_visible(False)
        plt.xticks(fontsize=32, rotation=45)  # 调整字体大小（数值越大字体越大）

        ax = plt.gca()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)  # 隐藏左边框

        # 调整布局避免标签被截断
        plt.tight_layout()

        # 保存图片到指定路径
        save_path = cache_path / "histogram.png"
        plt.savefig(save_path, bbox_inches="tight", pad_inches=0.1)  # 减少边缘留白)

        # 关闭图像释放资源
        plt.close()


def snapshot_to_pngs(snapshot, cache_path: str, normalize=False):
    """
    Convert a 3D/4D snapshot ndarray into per-slice PNG files.

    - snapshot is expected with axes order X, Y, Z, (C optional).
    - Writes files snapshot_0.png ... snapshot_{Z-1}.png into cache_path.
    - Uses ndarray_to_png to perform the per-slice conversion.

    Parameters:
    - snapshot: numpy ndarray (X, Y, Z[, C])
    - cache_path: directory where generated PNGs are stored.
    """
    cache_path = Path(cache_path)
    cache_path.mkdir(parents=True, exist_ok=True)

    if normalize:
        mn = float(np.percentile(snapshot, 50))
        mx = float(np.percentile(snapshot, 99))
        if mx - mn > 1e-8:
            snapshot = (snapshot - mn) / (mx - mn)
        else:
            snapshot = np.clip(snapshot, 0.0, 1.0)

    shape = snapshot.shape
    for zidx in range(shape[2]):
        array = snapshot[:, :, zidx, :]
        ndarray_to_png(array, str(cache_path / f"snapshot_{zidx}.png"))


def get_layer_caches() -> List[Dict[str, Any]]:
    """
    Read the saved layer metadata list from Blender's internal text datablock.

    - Looks for a text datablock named by LAYERS_JSON ("bioxel_layers").
    - Returns the parsed list of layer dictionaries if present; otherwise returns an empty list.

    Returns:
    - list of layer metadata dictionaries (possibly empty)
    """
    # 检查文本数据块是否存在
    if LAYERS_JSON not in bpy.data.texts:
        return []

    # 加载并解析数据
    layers_text = bpy.data.texts[LAYERS_JSON]
    try:
        layers_data = json.loads(layers_text.as_string())
        # 确保返回格式为列表
        return layers_data if isinstance(layers_data, list) else []
    except:
        return []


def set_layer_caches(layers_data: List[Dict[str, Any]]):
    """
    Write the provided list of layer metadata dictionaries into the Blender text datablock.

    - Ensures the LAYERS_JSON text datablock exists, then overwrites it with pretty JSON.

    Parameters:
    - layers_data: list of serializable dictionaries describing the layers
    """
    # 获取或创建文本数据块
    if LAYERS_JSON not in bpy.data.texts:
        bpy.data.texts.new(LAYERS_JSON)
    layers_text = bpy.data.texts[LAYERS_JSON]
    # 写入数据
    layers_text.clear()
    layers_text.write(json.dumps(layers_data, indent=4))


def save_layers_to_cache(layers: List[Layer], cache_dir: str) -> List[Dict[str, Any]]:
    """
    Save multiple Layer objects into cache folders.

    For each layer:
    - Generates a unique cache id.
    - Writes VDB files and a low-resolution snapshot (.npy) plus PNG slices under cache_dir/<cache_id>/.

    Returns:
    - List of layer cache metadata dictionaries.
    """
    cache_infos = []

    cache_dir_path = Path(cache_dir)
    cache_dir_path.mkdir(parents=True, exist_ok=True)

    for idx, layer in enumerate(layers):
        cache_id = str(int(time.time())) + str(idx)
        cache_path = cache_dir_path / str(cache_id)
        cache_layer_data(layer, cache_path)
        cache_layer_snapshot(layer, cache_path)

        # build layer_info
        cache_info = {
            "id": cache_id,
            "name": layer.name,
            "kind": layer.kind,
            "shape": layer.shape,
            "affine": layer.affine.tolist(),
            "bioxel_size": layer.bioxel_size[0],
            "dtype": layer.dtype.str,
            "dtype_num": layer.dtype.num,
            "frame_count": layer.frame_count,
            "channel_count": layer.channel_count,
            "offset": max(0, -layer.min),
            "min": layer.min,
            "max": layer.max,
            "path": bpy.path.abspath(str(cache_path)),
            "snapshot_z": 0.5,
        }

        cache_infos.append(cache_info)

    return cache_infos


def save_layers_to_json(layers: List[Layer], cache_dir: str) -> List[int]:
    """
    Save multiple Layer objects into cache folders and the internal layers text datablock.
    """
    existing_data = get_layer_caches()
    cache_infos = save_layers_to_cache(layers, cache_dir)

    added_ids = []
    for cache_info in cache_infos:
        existing_data.append(cache_info)
        added_ids.append(cache_info["id"])

    set_layer_caches(existing_data)
    print(f"Successfully added {len(added_ids)} layers to the internal text datablock")
    return added_ids
