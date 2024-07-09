[中文文档](https://uj6xfhbzp0.feishu.cn/wiki/Qx3VwHuNPimeI8kr6nDcvl1DnHf?from=from_copylink)

# 🦖 Bioxel Nodes

![Static Badge](https://img.shields.io/badge/Blender-orange?style=for-the-badge&logo=blender&logoColor=white)
![GitHub License](https://img.shields.io/github/license/OmooLab/BioxelNodes?style=for-the-badge)
![GitHub Release](https://img.shields.io/github/v/release/OmooLab/BioxelNodes?style=for-the-badge)
![GitHub Repo stars](https://img.shields.io/github/stars/OmooLab/BioxelNodes?style=for-the-badge)

Bioxel Nodes is a Blender addon for scientific volumetric data visualization. It using Blender's powerful Geometry Nodes and Cycles to process and render volumetric data. You are free to share your blender file to anyone who does not install this extension, since most processes were done by Blender's native nodes.

## About

Before us, there have been many tutorials and addons for importing volumetric data into Blender. However, we found that there were many scientific issues that were not addressed in place, and the volume render results were not epic. With Bioxel Nodes, you can easily import any format volumetric data into Blender, and more importantly, make a beautiful realistic volume rendering quickly.

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

-   Cycles CPUs only, Cycles GPUs (Optix), EEVEE (partial support)
-   Sections cannot be generated (will be supported soon)
-   Time sequence volume not supported (will be supported soon)

## Compatibility to Newer Version

Addon are updating, and it is possible that newer versions of the addon will not work on old project files properly. In order to make the old files work, you can do the following:

### For project files that need to be archived

Persistently save the Addon nodes before the addon is updated. This will put the nodes out of sync with the addon functionality, but it will ensure that the entire file can be calculated and rendered correctly, it fit to project files that you need to archive.
Bioxel Nodes > Save All Staged Data

### For working project files

If you've ever done a persistent save of Bioxel Nodes nodes, it's possible that after the addon update, there may be new features of the addon that don't synergize with the saved nodes. In order for the new version to work with the old nodes, you need to relink them.
Bioxel Nodes > Relink Nodes to Addon

## About EEVEE Render

Bioxel Nodes is designed for Cycles Render. However, it does support eevee render partially.Also, there are some limitations:

1. Only one cutter supported.
2. EEVEE Render result is not that great as Cycles does.

> Volume Shader is not work properly in EEVEE Next since 4.2. It is because EEVEE Next is not support attributes from instances of volume shader by now. But Blender 4.3 is ok, so I suppose this issue will eventually be fixed.
