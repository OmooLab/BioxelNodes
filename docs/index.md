**v2.0.X 已发布，仅支持 Blender 5.0+，使用方式和之前截然不同，也无法兼容旧版本文件。使用方式查看 http://docs.omoolab.xyz/bioxelnodes/2.0.x/basics/**

# Bioxel Nodes

[![For Blender](https://img.shields.io/badge/Blender-orange?style=for-the-badge&logo=blender&logoColor=white&color=black)](https://blender.org/)
![GitHub License](https://img.shields.io/github/license/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)
![GitHub Release](https://img.shields.io/github/v/release/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)
![GitHub Repo stars](https://img.shields.io/github/stars/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)

[![Discord](https://img.shields.io/discord/1265129134397587457?style=for-the-badge&logo=discord&label=Discord&labelColor=white&color=black)](https://discord.gg/pYkNyq2TjE)

Bioxel Nodes 是一款用于科学体数据可视化的 Blender 插件。它利用 Blender 强大的 **几何节点 (Geometry Nodes)** 和 **Cycles** 渲染器来处理和渲染体数据。

![cover](https://omoolab.github.io/BioxelNodes/latest/assets/cover.png)

- 逼真的渲染效果，同时也支持 EEVEE NEXT
- 支持多种数据格式
- 支持 4D 体数据
- 多种切割工具
- 简洁而强大的节点系统
- 基于 Blender 原生开发，插件卸载后仍可正常工作

**阅读[安装指南](installation.md)开始您的体数据可视化之旅！**

如果您在使用过程中遇到任何问题，欢迎加入我们的 [Discord 服务器](https://discord.gg/pYkNyq2TjE)。

## 支持多种格式

| 格式  | 扩展名                                   |
| ----- | ---------------------------------------- |
| DICOM | .dcm, .DCM, .DICOM, .ima, .IMA           |
| BMP   | .bmp, .BMP                               |
| JPEG  | .jpg, .JPG, .jpeg, .JPEG                 |
| PNG   | .png, .PNG                               |
| TIFF  | .tif, .TIF, .tiff, .TIFF                 |
| Nifti | .nia, .nii, .nii.gz, .hdr, .img, .img.gz |
| Nrrd  | .nrrd, .nhdr                             |
| HDF5  | .hdf, .h4, .hdf4, .he2, .h5, .hdf5, .he5 |
| OME   | .ome.tiff, .ome.tif                      |
| MRC   | .mrc, .mrc.gz, .map, .map.gz             |

## 支持 4D 体数据

![4d](https://omoolab.github.io/BioxelNodes/latest/assets/4d-time.gif)

4D 体数据也可以导入到 Blender 中。

## 支持 EEVEE NEXT

![eevee](https://omoolab.github.io/BioxelNodes/latest/assets/eevee.gif)

EEVEE NEXT 太棒了！Bioxel Nodes 现在全面支持 EEVEE NEXT！

## 路线图

- 更完善的多格式导入体验
- 一键烘焙带纹理模型
- AI 分割生成标签
