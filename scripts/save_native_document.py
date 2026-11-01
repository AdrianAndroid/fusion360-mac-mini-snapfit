app = adsk.core.Application.get()
doc = app.activeDocument
hub = app.data.dataHubs.item(0)
project = next(p for p in hub.dataProjects if p.name == 'Default Project')
folder = project.rootFolder
name = 'Mac mini 便携收纳盒'
existing = [f.name for f in folder.dataFiles if f.name == name]
if existing:
    raise RuntimeError('目标项目已存在同名文件，已停止以避免覆盖')
if not doc.saveAs(name, folder, '六步参数化模型；本地另有逐步 F3D 检查点', ''):
    raise RuntimeError('Fusion 原生 SaveAs 返回失败')
design = adsk.fusion.Design.cast(app.activeProduct)
print({'saved': doc.isSaved, 'document_name': doc.name,
       'hub': hub.name, 'project': project.name,
       'body_count': design.rootComponent.bRepBodies.count})
