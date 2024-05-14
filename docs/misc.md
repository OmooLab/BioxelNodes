# Future Features

- Support more volumetric data formats (.map, .txm...)
- Generate sections
- More segmentation methods, e.g. AI segmentation.
- Even better shader for volumetric rendering

### Bioxels

Bioxels is based on the RAS coordinate system, Right Aanterior Superior, which was chosen over LPS because it is more compatible with most 3D CG software coordinate systems, and is in line with the 3D artist's understanding of space.

All distances within Bioxels are in Units, and are specified in Meter pre unit. However, when Bioxels is imported into 3D CG software, its size in the software is not scaled by reading the Meter pre unit directly. The reason for this is that many 3D operations in software require that the primtives not be too large or too small.

### Based on OpenVDB

Bioxels is based entirely on OpenVDB for storage and rendering. The main reason for choosing OpenVDB is that as a volumetric data format, it is the fastest way to work with most CG renderers.

### Based on Geometry Nodes

Bioxel Nodes relies on Blender Geometry Nodes to reconstruct and render volumetric data. Node-based operations ensure that the original data is not permanently altered during reconstruction and rendering operations. The fact that the processing is based on Geometry Nodes without any additional dependencies also ensures that Blender can open files without this plugin installed. Look for more support for OpenVDB in GeometryNodes so that Bioxel Nodes can do more in the future.
