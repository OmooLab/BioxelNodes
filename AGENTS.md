# Bioxel Nodes

## 项目概览

Bioxel Nodes 是一个基于 Blender 的科学体数据可视化插件，利用 Blender 自带的 Geometry Nodes 与 Cycles（同时支持 EEVEE NEXT）处理并渲染体数据。

- 支持格式：`.dcm`、`.tif`/`.tiff`、`.nii`/`.nii.gz`、`.nrrd`、`.ome.tiff`、`.mrc`、`.h5` 等，完整列表见 `src/bioxelnodes/bioxel/data.py` 的 `SUPPORT_EXTS`
- 支持 4D 体数据（多帧 / 多通道 / 时间序列）
- v2.0.x 仅支持 Blender 5.0+
- 核心依赖：SimpleITK、pyometiff、mrcfile、h5py、numpy、scipy、transforms3d、matplotlib

## 构建、测试与开发命令

- 环境：Python 3.11，依赖由 uv 管理（`uv.lock`）
- `uv sync` 安装 / 同步依赖
- `uv run pytest` 运行测试（当前暂无测试用例）
- `uv run mkdocs serve` 本地预览文档；`uv run mkdocs build` 构建到 `site/`
- `uv run mike deploy <version> -p` 发布版本化文档
- `uv run build.py <platform> 3.11` 下载第三方 wheel 并更新 `src/bioxelnodes/blender_manifest.toml`，`platform` 取 `windows-x64` / `linux-x64` / `macos-arm64` / `macos-x64`
- `python pack.py <platform> [output.zip]` 将 `src/bioxelnodes` 打包为 zip
- 发布：推送 `v*` 标签触发 `.github/workflows/release.yml`，产物命名 `BioxelNodes.<version>.<platform>.zip`

## 架构

```text
src/bioxelnodes/            插件包根目录
├── __init__.py             入口：register/unregister、CLI 命令与 WindowManager 属性
├── auto_load.py            自动发现并按拓扑排序注册 bpy 类
├── constants.py            常量（节点库路径等）
├── preferences.py          AddonPreferences（缓存目录）
├── props.py                PropertyGroup / UIList / 属性更新回调
├── menus.py                菜单与右键菜单
├── panels.py               面板
├── asset_library.py        "O Bioxel" 资产库管理
├── node.py                 节点组加载与添加
├── layer.py                VDB 缓存、快照、图层元数据（text datablock JSON）
├── utils.py                通用工具（进度、对象查找、驱动等）
├── exceptions.py           向后兼容占位（自定义异常已改用内置异常）
├── blender_manifest.toml   Blender 扩展清单
├── assets/O_Bioxel/        节点库 .blend 与资产目录
├── wheels/                 随扩展分发的第三方 wheel
├── bioxel/                 核心数据模型（不依赖 Blender）
│   ├── data.py             Data 类与解析（read / read_meta）
│   ├── parse.py            解析函数（parse_volumetric_data 等）
│   ├── layer.py            Layer：TXYZC 顺序 ndarray + affine 变换
│   ├── container.py        Container：name + layers
│   └── io.py               HDF5 读写 Container
└── operators/              Operator 实现
    ├── io.py               导入 / 导出算子，启动后台导入进程
    ├── io_worker.py        后台 CLI 导入 worker（bioxelnodes_import_worker）
    ├── layer.py            图层管理算子
    ├── node.py             AddNode
    ├── structure.py        ExtractMesh
    └── misc.py             杂项算子
```

数据流：导入时主进程通过 `operators/io.py` 启动一个后台 Blender 子进程（`blender --background --command bioxelnodes_import_worker`），由 `io_worker.py` 解析数据、生成 `Layer`，写为 VDB 缓存，并通过 JSON 文件（`progress.json` / `result.json` / `cancel`）回传进度与结果，避免阻塞 UI。

仓库根目录另有 `docs/`（mkdocs-material 文档，中英双语）、`openspec/`（spec-driven 变更流程）、`.agents/`（技能定义）。

## 总规范

- 说明性内容（例如提交说明、文档、注释、mermaid），以中文为主，专有名词、约定俗称可用英文

## Markdown 规范

- 不使用`---`分割器
- `# Heading` 一级标题仅用于开头
- mermaid 节点名用英文字符

## 代码规范

- 避免嵌套结构
- 特殊的、非常规的需要写注释
- 变量、函数名、Docstring 用全英文
- 同一事物用统一表达
- 使用的依赖越少越好
- 选用简单直接的方式实现
- 代码、执行方式改变，调整已有的文档、计划，而非新建

## Shell 规范

- 优先使用、提供 Git Bash 执行所有 Shell 命令
- Windows 路径在 Bash 命令中优先使用正斜杠形式

## Blender 开发规范

- 插件、资产库压缩包名用大驼峰，如果需要，用`b45`来表示适用blender版本。比如`OmooLab.v0.1.0.b45.zip`
- Operator、Menu、Panel、AddonPreferences... Class 用大驼峰命名，不加任何前缀。Operator 动宾结构，比如`RenderImage`。Menu、Panel 以它们本身为后缀，比如`RenderPanel`
- 根据项目名提炼项目缩写，作为 bl_idname 和 自定义 Property 的前缀以区分其他功能和属性，以`Omoo`为例
  - bl_idname 用下划线小写命名，Operator 的 bl_idname 以`omoo.*`为前缀，比如`omoo.render_panel`；Menu 的以`OMOO_MT_*`为前缀；Panel 的以`OMOO_PT_*`为前缀。比如`OMOO_PT_render_panel`
  - 自定义 Property 用下划线小写命名，以`omoo_*`为前缀。比如`omoo_progress_factor`