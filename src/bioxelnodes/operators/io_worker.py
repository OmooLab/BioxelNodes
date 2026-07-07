import json
import sys
import traceback
from pathlib import Path

import numpy as np
import transforms3d

if __package__:
    from ..bioxel.layer import Layer
    from ..bioxel.parse import parse_volumetric_data
    from ..layer import save_layers_to_cache
else:
    PACKAGE_PARENT = Path(__file__).resolve().parents[2]
    if str(PACKAGE_PARENT) not in sys.path:
        sys.path.insert(0, str(PACKAGE_PARENT))

    from bioxelnodes.bioxel.layer import Layer
    from bioxelnodes.bioxel.parse import parse_volumetric_data
    from bioxelnodes.layer import save_layers_to_cache


def get_layer_shape(bioxel_size: float, orig_shape: tuple, orig_spacing: tuple):
    shape = (
        int(orig_shape[0] / bioxel_size * orig_spacing[0]),
        int(orig_shape[1] / bioxel_size * orig_spacing[1]),
        int(orig_shape[2] / bioxel_size * orig_spacing[2]),
    )

    return (
        shape[0] if shape[0] > 0 else 1,
        shape[1] if shape[1] > 0 else 1,
        shape[2] if shape[2] > 0 else 1,
    )


def write_json(path: Path, data):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data), encoding="utf-8")
    temp_path.replace(path)


def check_cancel(cancel_path: Path):
    if cancel_path.exists():
        raise KeyboardInterrupt("Cancelled by user")


def make_progress_writer(progress_path: Path, cancel_path: Path, scale=1.0, offset=0.0):
    def progress_callback(factor, text):
        check_cancel(cancel_path)
        write_json(
            progress_path,
            {
                "factor": offset + factor * scale,
                "text": text,
            },
        )

    return progress_callback


def progress_callback_factory(progress_path: Path, cancel_path: Path, layer_name, progress, progress_step):
    def progress_callback(frame, total):
        check_cancel(cancel_path)
        sub_progress_step = progress_step / total
        sub_progress = progress + frame * sub_progress_step
        text = f"Processing {layer_name} Frame {frame+1}..."
        write_json(progress_path, {"factor": sub_progress, "text": text})
        print(text)

    return progress_callback


def read_meta(config, progress_path: Path, cancel_path: Path):
    progress_callback = make_progress_writer(progress_path, cancel_path)
    series_id = config["series_id"] if config["series_id"] != "empty" else ""
    data, meta = parse_volumetric_data(
        data_file=config["filepath"],
        series_id=series_id,
        progress_callback=progress_callback,
    )
    check_cancel(cancel_path)
    return {
        "meta": {
            **meta,
            "spacing": list(meta["spacing"]),
            "affine": meta["affine"].tolist(),
            "xyz_shape": list(meta["xyz_shape"]),
        },
        "label_count": int(np.max(data)),
        "dtype": data.dtype.str,
        "dtype_kind": data.dtype.kind,
    }


def build_layers(config, progress_path: Path, cancel_path: Path):
    write_json(progress_path, {"factor": 0.0, "text": "Parsing Volumetirc Data..."})
    progress_callback = make_progress_writer(progress_path, cancel_path, scale=0.2)
    data, meta = parse_volumetric_data(
        data_file=config["filepath"],
        series_id=config["series_id"],
        progress_callback=progress_callback,
    )

    check_cancel(cancel_path)
    orig_shape = tuple(config["orig_shape"])
    orig_spacing = tuple(config["orig_spacing"])
    shape = get_layer_shape(config["bioxel_size"], orig_shape, orig_spacing)

    mat_scale = transforms3d.zooms.zfdir2aff(config["bioxel_size"])
    affine = np.dot(meta["affine"], mat_scale)
    kind = config["read_as"].lower()

    check_cancel(cancel_path)
    frame_source = config["frame_source"]
    if frame_source == "-1":
        data = data[0:1, :, :, :, :]
    elif frame_source == "0":
        pass
    elif frame_source == "1":
        data = data.transpose(1, 0, 2, 3, 4)
        shape = (1, shape[1], shape[2])
    elif frame_source == "2":
        data = data.transpose(2, 1, 0, 3, 4)
        shape = (shape[0], 1, shape[2])
    elif frame_source == "3":
        data = data.transpose(3, 1, 2, 0, 4)
        shape = (shape[0], shape[1], 1)
    else:
        data = data.transpose(4, 1, 2, 3, 0)

    layers = []
    if kind == "label":
        name = config["layer_name"] or "Label"
        data = data.astype(int)
        label_count = int(np.max(data))
        progress_step = 0.7 / label_count

        for i in range(label_count):
            check_cancel(cancel_path)
            name_i = f"{name}_{i+1}"
            progress = 0.2 + i * progress_step
            write_json(progress_path, {"factor": progress, "text": f"Processing {name_i}..."})
            progress_callback = progress_callback_factory(
                progress_path, cancel_path, name_i, progress, progress_step
            )
            label_data = data == np.full_like(data, i + 1)
            layer = Layer(data=label_data, name=name_i, kind=kind)
            layer.resize(
                shape=shape,
                smooth=config["smooth"],
                progress_callback=progress_callback,
            )
            layer.affine = affine
            layers.append(layer)

    if kind == "color":
        if np.issubdtype(np.uint8, data.dtype):
            data = np.multiply(data, 1.0 / 256, dtype=np.float32)
        elif data.dtype.kind in ["u", "i"]:
            data = data.astype(np.float32)
            min_val = data.min()
            max_val = data.max()
            if max_val != min_val:
                data = (data - min_val) / (max_val - min_val)
            else:
                data = np.zeros_like(data, dtype=np.float32)
        else:
            data = data.astype(np.float32)

        name = config["layer_name"] or "Color"
        if data.shape[4] == 1:
            data = np.repeat(data, repeats=3, axis=4)
        elif data.shape[4] == 2:
            d_shape = list(data.shape)
            d_shape = d_shape[:4] + [1]
            zore = np.zeros(tuple(d_shape), dtype=np.float32)
            data = np.concatenate((data, zore), axis=-1)
        elif data.shape[4] > 3:
            data = data[:, :, :, :, :3]

        check_cancel(cancel_path)
        write_json(progress_path, {"factor": 0.2, "text": f"Processing {name}..."})
        progress_callback = progress_callback_factory(progress_path, cancel_path, name, 0.2, 0.7)
        layer = Layer(data=data, name=name, kind=kind)
        layer.resize(shape=shape, progress_callback=progress_callback)
        layer.affine = affine
        layers.append(layer)

    elif kind == "scalar":
        name = config["layer_name"] or "Scalar"

        if config["remap"]:
            data = data.astype(np.float32)
            min_val = data.min()
            max_val = data.max()
            if max_val != min_val:
                data = (data - min_val) / (max_val - min_val)
            else:
                data = np.zeros_like(data, dtype=np.float32)

        if config["split_channel"]:
            progress_step = 0.7 / config["channel_count"]

            for i in range(config["channel_count"]):
                check_cancel(cancel_path)
                name_i = f"{name}_{i+1}"
                progress = 0.2 + i * progress_step
                write_json(progress_path, {"factor": progress, "text": f"Processing {name_i}..."})
                progress_callback = progress_callback_factory(
                    progress_path, cancel_path, name_i, progress, progress_step
                )
                layer = Layer(data=data[:, :, :, :, i : i + 1], name=name_i, kind=kind)
                layer.resize(shape=shape, progress_callback=progress_callback)
                layer.affine = affine
                layers.append(layer)
        else:
            check_cancel(cancel_path)
            write_json(progress_path, {"factor": 0.2, "text": f"Processing {name}..."})
            progress_callback = progress_callback_factory(progress_path, cancel_path, name, 0.2, 0.7)
            layer = Layer(data=data, name=name, kind=kind)
            layer.resize(shape=shape, progress_callback=progress_callback)
            layer.affine = affine
            layers.append(layer)

    check_cancel(cancel_path)
    write_json(progress_path, {"factor": 0.9, "text": "Creating Layers..."})
    cache_infos = save_layers_to_cache(layers, config["cache_dir"])
    return {"cache_infos": cache_infos, "added_ids": [item["id"] for item in cache_infos]}


def main():
    config_path = Path(sys.argv[-1])
    config = json.loads(config_path.read_text(encoding="utf-8"))
    progress_path = Path(config["progress_path"])
    result_path = Path(config["result_path"])
    cancel_path = Path(config["cancel_path"])

    try:
        if config["command"] == "read_meta":
            result = read_meta(config, progress_path, cancel_path)
        elif config["command"] == "import_layers":
            result = build_layers(config, progress_path, cancel_path)
        else:
            raise ValueError(f"Unknown command: {config['command']}")

        write_json(result_path, {"ok": True, **result})
        write_json(progress_path, {"factor": 1.0, "text": ""})
    except KeyboardInterrupt:
        write_json(result_path, {"ok": False, "cancelled": True})
    except Exception as e:
        write_json(
            result_path,
            {
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )


if __name__ == "__main__":
    main()
