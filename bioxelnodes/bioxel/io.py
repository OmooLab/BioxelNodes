from pathlib import Path
import uuid


# 3rd-party
import h5py

from .container import Container
from .layer import Layer


def load_container(load_file: str):
    load_path = Path(load_file).resolve()
    with h5py.File(load_path, 'r') as file:
        layers = []
        for key, layer_dset in file['layers'].items():
            layers.append(Layer(data=layer_dset[:],
                                name=layer_dset.attrs['name'],
                                kind=layer_dset.attrs['kind'],
                                affine=layer_dset.attrs['affine']))

        container = Container(name=file.attrs['name'],
                              layers=layers)

        return container


def save_container(container: Container, save_file: str, overwrite=False):
    save_path = Path(save_file).resolve()
    if overwrite:
        if save_path.is_file():
            save_path.unlink()

    with h5py.File(save_path, "w") as file:
        file.attrs['name'] = container.name
        layer_group = file.create_group("layers")
        for layer in container.layers:
            layer_key = uuid.uuid4().hex[:8]
            layer_dset = layer_group.create_dataset(name=layer_key,
                                                    data=layer.data)
            layer_dset.attrs['name'] = layer.name
            layer_dset.attrs['kind'] = layer.kind
            layer_dset.attrs['affine'] = layer.affine
