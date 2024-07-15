# Prepare Your Data

## Support Formats

First thing first, you need to get your volumetric data ready in disk. Bioxel Nodes is developed based on Simple ITK, so theoretically all formats supported by Simple ITK are supported by the addon. If your data is not in the support list, you may do the data conversion first.

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

## Download Data from Internet

If you don't have any volumetric data, you can access open research data from list below.

> Note that just because they are open and available for download does not mean you can use them for anything! Be sure to look at the description of the available scopes from website.

| Source                                                                               | Object             |
| ------------------------------------------------------------------------------------ | ------------------ |
| [MorphoSource](https://www.morphosource.org/)                                        | Open Research Data |
| [Dryad](https://datadryad.org)                                                       | Open Research Data |
| [OpenOrganelle](https://openorganelle.janelia.org/datasets)                          | Cells              |
| [Embodi3D](https://www.embodi3d.com/files/category/37-medical-scans/)                | Medical Images     |
| [Github](https://github.com/sfikas/medical-imaging-datasets)                         | Medical Images     |
| [NIHR](https://nhsx.github.io/open-source-imaging-data-sets/)                        | Medical Images     |
| [Medical Segmentation Decathlon](http://medicaldecathlon.com/)                       | Medical Images     |
| [Allen Cell Explorer](https://www.allencell.org/3d-cell-viewer.html)                 | Cells              |
| [Visible Human Project](https://www.nlm.nih.gov/research/visible/visible_human.html) | Medical Images     |
