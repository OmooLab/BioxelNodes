from .layer import Layer


class Container():
    def __init__(self,
                 name,
                 layers: list[Layer] = []) -> None:
        self.name = name
        self.layers = layers
