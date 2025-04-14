[中文文档](https://uj6xfhbzp0.feishu.cn/wiki/LPKEwjooSivxjskWHlCcQznjnNf?from=from_copylink)

# Bioxel Nodes

[![For Blender](https://img.shields.io/badge/Blender-orange?style=for-the-badge&logo=blender&logoColor=white&color=black)](https://blender.org/)
![GitHub License](https://img.shields.io/github/license/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)
![GitHub Release](https://img.shields.io/github/v/release/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)
![GitHub Repo stars](https://img.shields.io/github/stars/OmooLab/BioxelNodes?style=for-the-badge&labelColor=black)

[![Discord](https://img.shields.io/discord/1265129134397587457?style=for-the-badge&logo=discord&label=Discord&labelColor=white&color=black)](https://discord.gg/pYkNyq2TjE)

Bioxel Nodes is a Blender addon for scientific volumetric data visualization. It using Blender's powerful **Geometry Nodes** and **Cycles** to process and render volumetric data.

![cover](https://omoolab.github.io/BioxelNodes/latest/assets/cover.png)

## Features

-   Realistic rendering result, also support EEVEE NEXT.
-   Support many formats：.dcm, .jpg, .tif, .nii, .nrrd, .ome, .mrc...
-   Support 4D volumetric data.
-   Many kinds of cutters.
-   Simple and powerful nodes.
-   Based on blender natively, can work without addon.

| ![4D](https://omoolab.github.io/BioxelNodes/latest/assets/4d-time.gif) | ![EEVEE](https://omoolab.github.io/BioxelNodes/latest/assets/eevee.gif) |
| :--------------------------------------------------------------------: | :---------------------------------------------------------------------: |
|                       Support 4D volumetric data                       |                       Real-time render with eevee                       |

**Read the [getting started](https://omoolab.github.io/BioxelNodes/latest/installation) to begin your journey into visualizing volumetric data!**

Welcome to our [discord server](https://discord.gg/pYkNyq2TjE), if you have any problems with this add-on.

## Citation

If you want to cite this work, you can cite it from Zenodo:

[![DOI](https://zenodo.org/badge/786623459.svg)](https://zenodo.org/badge/latestdoi/786623459)

## Known Limitations

-   Only one cutter supported in EEVEE render
-   Shader fail to work when convert to mesh.
-   Section surface cannot be generated when convert to mesh (will be supported soon)

## Roadmap

-   Better multi-format import experience
-   One-click bake model with texture
-   AI Segmentation to Generate Labels
