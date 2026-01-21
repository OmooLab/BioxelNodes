# BioxelNodes - Agent Development Guide

This file contains essential information for agentic coding agents working on the BioxelNodes codebase.

## Project Overview

BioxelNodes is a Blender addon for scientific volumetric data visualization. It integrates with Blender's Geometry Nodes and Cycles rendering engine to process and visualize medical/scientific data.

**Language:** Python 3.11
**Framework:** Blender Python API (bpy)
**Package Manager:** uv

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync
```

### Build Commands
```bash
# Build for specific platform
uv run build.py <platform>  # platforms: windows-x64, linux-x64, macos-arm64, macos-x64
```

### Code Quality
```bash
# Format code (autopep8)
autopep8 --in-place --recursive src/
```

### Documentation
```bash
# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mike deploy --push --update-aliases 0.2.x latest
```

## Code Style Guidelines

### Formatting
- **4-space indentation**
- **PEP 8** compliance enforced via autopep8

### Naming Conventions
- **snake_case** for functions, variables, and files
- **PascalCase** for classes (Blender convention)
- **UPPER_CASE** for constants
- **bioxel_** prefix for addon-specific properties

### Import Organization
```python
# Standard library imports first
import pathlib
import uuid

# Third-party imports
import bpy
import numpy as np
import SimpleITK as sitk

# Relative imports for internal modules
from ..exceptions import CancelledByUser
from ..utils import get_layer_obj
```

### Type Hints
- Use sparingly, mainly for Blender property annotations
- Focus on function signatures and complex data structures
- Example: `def process_data(data: np.ndarray) -> np.ndarray:`

## Architecture Patterns

### Auto-Registration System
- Uses `auto_load.py` for automatic class registration
- Classes are discovered automatically via reflection
- Registration order resolved via topological sorting
- All Blender classes must inherit from appropriate base types

### Module Structure
```
src/bioxelnodes/
├── __init__.py           # Addon entry point, asset library setup
├── auto_load.py          # Auto-registration system
├── constants.py          # Constants and paths
├── utils.py              # Utility functions
├── preferences.py        # Addon preferences
├── props.py              # Blender properties
├── panels.py             # UI panels
├── menus.py              # UI menus
├── node.py               # Node utilities
├── layer.py              # Layer management
├── operators/            # Blender operators
├── bioxel/               # Core bioxel functionality
└── assets/               # Blender assets and node libraries
```

### Blender Integration Patterns

#### Property Groups
```python
class BioxelProperties(bpy.types.PropertyGroup):
    bl_label = "Bioxel Properties"
    
    bioxel_custom_prop: bpy.props.StringProperty(
        name="Custom Property",
        default="",
        description="Description for UI"
    )
```

#### Operators
```python
class BIOXEL_OT_custom_operator(bpy.types.Operator):
    bl_idname = "bioxel.custom_operator"
    bl_label = "Custom Operator"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Operator logic here
        return {'FINISHED'}
```

#### Panels
```python
class BIOXEL_PT_custom_panel(bpy.types.Panel):
    bl_label = "Custom Panel"
    bl_idname = "BIOXEL_PT_custom_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bioxel"
    
    def draw(self, context):
        layout = self.layout
        # UI drawing code here
```

## Error Handling

### Error Handling Patterns
- Use try-catch blocks for file operations
- Handle user cancellation gracefully
- Report progress for long operations using `bioxel_progress_factor` and `bioxel_progress_text`
- Log warnings with print statements for debugging


## Key Dependencies

### Core Libraries
- **bpy** (Blender Python API) - Core integration
- **numpy** - Array processing
- **SimpleITK** - Medical image processing
- **h5py** - HDF5 file handling

### Scientific Libraries
- **matplotlib** - Plotting and visualization
- **transforms3d** - 3D transformations
- **pyometiff** - OME-TIFF support
- **mrcfile** - MRC file format support

## Development Workflow

### Making Changes
1. Identify the appropriate module (operators, panels, bioxel, etc.)
2. Follow existing naming conventions and patterns
3. Use auto-registration - no manual registration needed
4. Test with Blender's Python console
5. Format code with autopep8 before committing

### Adding New Features
1. Create appropriate classes in relevant modules
2. Use proper prefixes (BIOXEL_OT_, BIOXEL_PT_, etc.)
3. Add to auto_load system automatically discovers new classes
4. Update documentation if needed

### File Operations
- Use `pathlib.Path` for path operations
- Check file existence before operations
- Handle permissions and missing files gracefully
- Use appropriate file formats (HDF5 for data, PNG for images)

## Blender Integration Notes

### Asset Library
- Automatically managed via `add_asset_library_if_missing()`
- Located at `NODE_LIB_DIRPATH`
- Uses "PACK" import method
- Name: "O Bioxel"

### Progress Reporting
- Use `bioxel_progress_factor` (0.0 to 1.0) for progress
- Use `bioxel_progress_text` for status messages
- Update via WindowManager properties

### Layer Management
- Layers stored as HDF5 files
- Container objects manage multiple layers
- Use `layer.py` for layer operations
- Support for various medical image formats

## Common Pitfalls

### Blender API
- Always check context validity
- Handle different Blender versions (check `bpy.app.version`)
- Use proper property types for UI
- Register classes in correct order (auto_load handles this)

### Performance
- Use NumPy for array operations
- Avoid expensive operations in UI draw calls
- Cache computed values where appropriate
- Use background threads for long operations

### File I/O
- Always close file handles
- Use context managers for file operations
- Handle large files in chunks
- Validate file formats before processing