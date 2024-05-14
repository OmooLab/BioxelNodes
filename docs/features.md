# Features & Options

## Import Volume Data as Biovels

File > Import > Volume Data as Biovels

### Resample

![alt text](assets/resample.png)

Sometimes the original data is too big, or the spacing in the original data is not reasonable, you can modify the `Bioxel Size` and `Original Spacing` to adjust the Shape of the Bixoels.

A bioxel is like a pixel, the larger the `Bioxel Size`, the lower the resolution of the image, Original Spacing will be read from the original data record, but sometimes the image doesn't have original spacing, you may need to input it manually to get the correct shape.

### Read as

#### as Scalar

![alt text](assets/as-scalar.png)

In some cases the environment value is higher than the value of the target object, you can check `Invert Scalar` to adjust the value for better result.

#### as Labels

![alt text](assets/as-labels.png)

Many AI segmentation task datasets, provide segmentation data, which are often an integer value representing a layer of segmentation labels. You can set the Label Index to determine exactly which labels to load.

#### as Vector (Not implemented)

#### as Color (Not implemented)

### Others

![alt text](assets/import-others.png)

## Convert Bioxels to Mesh

In 3D view, select bioxels and right-click, Bioxels > Bioxels To Mesh

![alt text](assets/to-mesh.png)

## Export Biovels as VDB

File > Export > Biovels as VDB
