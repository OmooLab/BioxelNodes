[中文文档](https://uj6xfhbzp0.feishu.cn/wiki/Qx3VwHuNPimeI8kr6nDcvl1DnHf?from=from_copylink)

# 🦖 Bioxel Nodes

![Static Badge](https://img.shields.io/badge/Blender-orange?style=for-the-badge&logo=blender&logoColor=white)
![GitHub License](https://img.shields.io/github/license/OmooLab/BioxelNodes?style=for-the-badge)
![GitHub Release](https://img.shields.io/github/v/release/OmooLab/BioxelNodes?style=for-the-badge)
![GitHub Repo stars](https://img.shields.io/github/stars/OmooLab/BioxelNodes?style=for-the-badge)

Bioxel Nodes is a Blender extension for scientific volumetric data visualization. It using Blender's powerful Geometry Nodes and Cycles to process and render volumetric data. You are free to share your blender file to anyone who does not install this extension, since most processes were done by Blender's native nodes.

## About

Before us, there have been many tutorials and extensions for importing volumetric data into Blender. However, we found that there were many scientific issues that were not addressed in place, and the volume render results were not epic. With Bioxel Nodes, you can easily import any format volumetric data into Blender, and more importantly, make a beautiful realistic volume rendering quickly.

Below are some examples with Bioxel Nodes. Thanks to Cycles Render, the volumetric data can be rendered with great detail:

![cover](https://omoolab.github.io/BioxelNodes/latest/assets/cover.png)

So how to use this extension? please check [Getting Started](https://omoolab.github.io/BioxelNodes/latest/getting-started)

## Supported Format

| Format | EXT                                      | Test    |
| ------ | ---------------------------------------- | ------- |
| DICOM  | .dcm, .DICOM                             | ✅ pass |
| BMP    | .bmp, .BMP                               | ✅ pass |
| JPEG   | .jpg, .JPG, .jpeg, .JPEG                 | ✅ pass |
| PNG    | .png, .PNG                               | ✅ pass |
| TIFF   | .tif, .TIF, .tiff, .TIFF                 | ✅ pass |
| Nifti  | .nia, .nii, .nii.gz, .hdr, .img, .img.gz | ✅ pass |
| Nrrd   | .nrrd, .nhdr                             | ✅ pass |
| Meta   | .mha, .mhd                               | yet     |
| HDF5   | .hdf, .h4, .hdf4, .he2, .h5, .hdf5, .he5 | ✅ pass |
| VTK    | .vtk                                     | yet     |
| BioRad | .PIC, .pic                               | yet     |
| Gipl   | .gipl, .gipl.gz                          | yet     |
| LSM    | .lsm, .LSM                               | yet     |
| MINC   | .mnc, .MNC                               | yet     |
| MRC    | .mrc, .rec                               | yet     |

## Known Limitations

-   Sections cannot be generated (will be supported soon)
-   Time sequence volume not supported (will be supported soon)

## Upgrade from 0.1.x to 0.2.x

You need to do the following:

1. Remove the old version of Bioxel Nodes at Preferences > Add-ons
2. Add the new version and restart Blender.

It is not support editing the same blender file across extension versions. In order to make sure that the previous file works properly. You need to save the staged data before upgrading ( read the last section of [Getting Started](https://omoolab.github.io/BioxelNodes/latest/getting-started/#share-your-file) ).

But even then, there is still no guarantee that the new version of the extension will work on the old blender file. Therefore, it is highly recommended to open a new blender file to start the creating, not based on the old one.

Alternatively, objects from the old file that have nothing to do with Bioxel Nodes could be append to the new blender file.

## About EEVEE Render

Bioxel Nodes is designed for Cycles Render. However, it does support eevee render partially. "Solid Shader" node and "Volume Shader" node have a toggle called "EEVEE Render". If you want to render Bioxel Component in real-time, turn it on.

Also, there are some limitations:

1. Only one cutter supported.
2. You cannot use "Color Ramp" over 2 colors.
3. EEVEE Render result is not that great as Cycles does.

> "Volume Shader" node is not work properly in EEVEE Next since 4.2. It is because EEVEE Next is not support attributes from instances of volume shader by now. But the Blender 4.2 docs still say attributes reading is ok, so I suppose this feature will eventually be implemented.
