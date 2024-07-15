# Installation

> **Currently only support Blender 4.1 or above, make sure you have the correct version of Blender.**

## For Blender 4.2 or higher

The most recommended way is to open **Edit > Preferences > Extension**, enter "bio" in the search box and click **Install**. since the addon is quite large (20MB) you may need to wait a while!

![extension](assets/installation_extension.png)

Thats it!

> If it cannot be enable, reboot blender or install again as administrator

Also, you can do it maually. Download the **Extension** version `BioxelNodes_Extension_{version}.zip` from https://github.com/OmooLab/BioxelNodes/releases/latest  
In Blender, **Edit > Preferences > Extensions > Install from Disk**, select the zip file you just downloaded.

## For Blender 4.1

Download the **Addon** version `BioxelNodes_Addon_{version}.zip` from https://github.com/OmooLab/BioxelNodes/releases/latest  
In Blender, Edit > Preferences > Add-ons > Install, select the zip file you just downloaded.

The add-on requires a third-party python dependency called SimpleITK, click `Install SimpleITK` button below to install the dependency. After clicking, blender may get stuck, it is downloading and installing, just wait for a moment. After that, click `Reboot Blender` button.

![dependency](assets/installation_dependency.png)

This step may have failed due to network factors, just click "Set PyPI Mirror" to change the mirror.
