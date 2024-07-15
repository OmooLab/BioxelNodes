
## First Time Import Volume Data

File > Import > Volume Data as Bioxel Layer

### Resample

![alt text](assets/features_resample.png)

Sometimes the original data is too big, or the spacing in the original data is not reasonable, you can modify the `Bioxel Size` and `Original Spacing` to adjust the Shape of the layer.

A bioxel is like a pixel, the larger the `Bioxel Size`, the lower the resolution of the image, Original Spacing will be read from the original data record, but sometimes the image doesn't have original spacing, you may need to input it manually to get the correct shape.

### Read as

-   as Scalar

    ![alt text](assets/features_as-scalar.png)

    In some cases the environment value is higher than the value of the target object, you can check `Invert Scalar` to adjust the value for better result.

-   as Labels

    Many AI segmentation task datasets, provide segmentation data, which are often an integer value representing a layer of segmentation labels. You can set it to `Labels` to load them.

-   _as Vector (Not implemented yet)_

-   _as Color (Not implemented yet)_

### Others

![alt text](assets/features_import-others.png)

`Scene Scale` determines how many units of length in the Blender world correspond to one unit of length in the Bioxel world. Since Blender defaults to meters, and the default size of blender primitives are around 1 blender unit. Therefore `Scene Scale` set to 0.01 is appropriate.

`Orient to RAS` determines whether the layer should be converted to the RAS coordinate system. Regardless of the format of the medical image data, the coordinate system is mostly the LPS coordinate system. Bioxel, however, are in the RAS coordinate system and therefore need to be transformed in most cases.

## Adding Volume Data to an existing container

In 3D view or outliner panel, select the container and right click, Bioxel Nodes > Add Volume Data to Container.
The import settings are the same as for the first time import.