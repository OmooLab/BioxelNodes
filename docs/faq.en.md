# FAQ

## Nothing in the scene when rendering?

If you're using the Cycles renderer with GPU, make sure your GPU supports "Optix", as Bioxel Nodes relies on OSL (Open shader language) for volumetric rendering, otherwise you'll have to use the CPU for rendering.

If you're using the EEVEE renderer, this issue is due to EEVEE not loading shaders for some unknown reason, save the file and restart Blender to fix it.

## After updating the addon, the nodes in the file have turned red?

This is because the version of the nodes in the file does not match the current version of the addon after updating.

If you still want to edit the file with Bioxel Nodes, you can only roll back the addon version to the version that corresponds to the nodes.

If you just want the file to work and you won't rely on Bioxel Nodes any more, then you can just click **Bioxel Nodes > Relink Node Library >** in the top menu and select the corresponding version. Check to see if the nodes are working and rendering properly, and when everything is OK, click **Bioxel Nodes > Save Node Library** and select the save location in the dialog box.
