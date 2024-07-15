# Concepts & Pipeline

## Container, Layer, Component

Bioxel Nodes imports volumetric data and put it into a **Container** as a **Layer**. One container may has more than one layer, and each layer stores the information of different fields under the same location, which is similar to the view layers in map app, except that here it is in 3D space.

In order to visualize the volumetric data the way we want it to, we need to build renderable objects from layers. We call those objects **Component**. The following diagram shows the relationship of **Container**, **Layer**, and **Component**:

![alt text](assets/features_concept.png)

### Container Structure

In Blender, container structure is like this:

```bash
Case_0000 # Container
|-- Case_0000_CT # Layer
|-- Case_0000_Label_1 # Layer
`-- Case_0000_Label_2 # Layer
```

The container also stores the build process in geometry nodes:

![alt text](assets/features_container.png)

### Layer Type
The layer is categorized into these by data type:

-   Scalar
-   Label
-   Vector (Not implemented yet)
-   Color (Not implemented yet)

## Component Building Pipline

In order to build a component, the general process is to first use a "Mask Method" node to build the surface of the component based on its layers, and then connect to a "Assign Shader" node to add the physical properties. Finally, if you need to cut the cross-section, then connect to a "Cut" node. The whole process is shown in the following diagram

![alt text](assets/nodes_concept.png)

A typical example looks like this:

![alt text](assets/nodes_example.png)

The "Mask Method" node tends to be very computationally intensive, and if it consumes too much time, then you can bake it with a "Bake" node after it (but you need to save the Blender file first).

![alt text](assets/nodes_bake.png)
