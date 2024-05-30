# Bioxel Nodes

![Static Badge](https://img.shields.io/badge/Blender-orange?style=for-the-badge&logo=blender&logoColor=white)
![GitHub License](https://img.shields.io/github/license/OmooLab/BioxelNodes?style=for-the-badge)
![GitHub Release](https://img.shields.io/github/v/release/OmooLab/BioxelNodes?style=for-the-badge)
![GitHub Repo stars](https://img.shields.io/github/stars/OmooLab/BioxelNodes?style=for-the-badge)

Bioxel Nodes is a Blender add-on for scientific volumetric data visualization. It using Blender's powerful Geometry Nodes | Cycles to process and render volumetric data.

## About

Before us, there have been many tutorials and add-ons for importing volumetric data into Blender. However, we found that there were many details that were not addressed in place, some scientific facts were ignored, and the volume rendering was not pretty enough. With Bioxel Nodes, you can easily import the volumetric data into Blender, and more importantly, it can quickly make a beautiful realistic rendering of it.

Below are some examples with Bioxel Nodes. Thanks to Cycles Render, the volumetric data can be rendered with great detail:

![gallery](assets/gallery.png)

The "Bioxel" in "Bioxel Nodes", is a combination of the words "Bio-" and "Voxel". Bioxel is a voxel that stores biological data. We are developing a toolkit around Bioxel for better biological data visualization. but before its release, we made this Blender version of bioxels toolkit first, in order to let more people to have fun with volumetric data. [Getting Started](https://omoolab.github.io/BioxelNodes/latest/getting-started)

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

## To Upgrade Add-on

To upgrade from an older version of the add-on to the latest, you need to do the following:

1. Remove the old version of Bioxel Nodes at Preferences > Add-ons
2. Add the new version and restart Blender.

It is not support editing the same blender file across add-on versions. In order to make sure that the previous file works properly. You need to save the staged data before upgrading ( read the last section of [Getting Started](https://omoolab.github.io/BioxelNodes/latest/getting-started/#share-your-file) ).

But even then, there is still no guarantee that the new version of the add-on will work on the old blender file. Therefore, it is highly recommended to open a new blender file to start the creating, not based on the old one.

Alternatively, objects from the old file that have nothing to do with Bioxel Nodes could be append to the new blender file.
