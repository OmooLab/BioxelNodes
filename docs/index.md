[中文文档](https://uj6xfhbzp0.feishu.cn/wiki/Qx3VwHuNPimeI8kr6nDcvl1DnHf?from=from_copylink)

# Bioxel Nodes

[![For Blender](https://img.shields.io/badge/Blender-orange?style=for-the-badge&logo=blender&logoColor=white&color=black)](https://blender.org/)
![GitHub License](https://img.shields.io/github/license/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)
![GitHub Release](https://img.shields.io/github/v/release/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)
![GitHub Repo stars](https://img.shields.io/github/stars/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)

[![Discord](https://img.shields.io/discord/1265129134397587457?style=for-the-badge&logo=discord&label=Discord&labelColor=white&color=black)](https://discord.gg/pYkNyq2TjE)

Bioxel Nodes is a Blender addon for scientific volumetric data visualization. It using Blender's powerful **Geometry Nodes** and **Cycles** to process and render volumetric data.

![cover](https://omoolab.github.io/BioxelNodes/latest/assets/cover.png)

-   Realistic rendering result, also support EEVEE NEXT.
-   Support multiple formats.
-   Support 4D volumetric data.
-   All kinds of cutters.
-   Simple and powerful nodes.
-   Based on blender natively, can work without addon.

**Read the [getting started](https://omoolab.github.io/BioxelNodes/latest/installation) to begin your journey into visualizing volumetric data!**

Welcome to our [discord server](https://discord.gg/pYkNyq2TjE), if you have any problems with this add-on.

## Support Multiple Formats

| Format | EXT                                      | Test    |
| ------ | ---------------------------------------- | ------- |
| DICOM  | .dcm, .DCM, .DICOM, .ima, .IMA           | ✅ pass |
| BMP    | .bmp, .BMP                               | ✅ pass |
| JPEG   | .jpg, .JPG, .jpeg, .JPEG                 | ✅ pass |
| PNG    | .png, .PNG                               | ✅ pass |
| TIFF   | .tif, .TIF, .tiff, .TIFF                 | ✅ pass |
| Nifti  | .nia, .nii, .nii.gz, .hdr, .img, .img.gz | ✅ pass |
| Nrrd   | .nrrd, .nhdr                             | ✅ pass |
| HDF5   | .hdf, .h4, .hdf4, .he2, .h5, .hdf5, .he5 | ✅ pass |
| OME    | .ome.tiff, .ome.tif                      | ✅ pass |
| MRC    | .mrc, .mrc.gz, .map, .map.gz             | ✅ pass |

## Support 4D volumetric data

![4d](https://omoolab.github.io/BioxelNodes/latest/assets/4d-time.gif)

🥰 4D volumetric data can also be imported into Blender.

## Support EEVEE NEXT

![eevee](https://omoolab.github.io/BioxelNodes/latest/assets/eevee.gif)

👍 EEVEE NEXT is absolutely AWESOME! Bioxel Nodes is fully support EEVEE NEXT now! However, there are some limitations:

1. Only one cutter supported.
2. EEVEE result is not that great as Cycles does.

## Known Limitations

-   Only works with Cycles CPU , Cycles GPU (OptiX), EEVEE
-   Section surface cannot be generated when convert to mesh (will be supported soon)

## Compatible to Newer Version

**v0.3.x is not compatible to v0.2.x, Updating this addon may break old files. Read the following carefully before upgradation**

Before upgradation, you need to ask yourself whether this project file will be modified again or not, if it's an archived project file, I would recommend that you run **Bioxel Nodes > Save Staged Data** to make the addon nodes permanent. In this way, there will be no potential problem with the nodes not functioning due to the addon update.

After the addon update, your old project files may not work either, this may be because you had executed **Save Staged Data**. If so, you need to execute **Bioxel Nodes > Relink Nodes to Addon** to relink them to make sure that the addon's new functionality and the addon nodes are synchronized.

Also, the older shaders are not based on OSL, so if you find that you can't render volumes, you need to turn on **Open Shading Language (OSL)** in the Render Settings.

## Roadmap

-   Better multi-format import experience
-   One-click bake model with texture
-   AI Segmentation to Generate Labels
