# 常见问题

## 渲染时场景什么都没有？

如果您使用 GPU 进行 Cycles 渲染，请确保您的 GPU 支持"Optix"，因为 Bioxel Nodes 依赖 OSL（Open Shader Language）进行体渲染，否则您必须使用 CPU 进行渲染。

如果您使用 EEVEE 渲染器，此问题是因为 EEVEE 出于未知原因未加载着色器，保存文件并重启 Blender 即可修复。

## 更新插件后，文件中的节点变红了？

这是因为文件中节点的版本与更新后插件的版本不匹配。

如果您仍想使用 Bioxel Nodes 编辑文件，只能将插件回滚到与节点对应的版本。

如果您只想让文件正常工作，不再依赖 Bioxel Nodes，那么您只需点击顶部菜单 **Bioxel Nodes > Relink Node Library >**，然后选择相应的版本。检查节点是否正常工作并正确渲染，一切正常后，点击 **Bioxel Nodes > Save Node Library**，在对话框中选择保存位置。