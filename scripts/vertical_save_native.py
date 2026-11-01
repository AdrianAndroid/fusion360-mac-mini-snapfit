app = adsk.core.Application.get()
doc = app.activeDocument
name = 'Mac mini 竖向收纳盒_300x210x210'
hub = app.data.dataHubs.item(0)
project = next(p for p in hub.dataProjects if p.name == 'Default Project')
folder = project.rootFolder
if doc.isSaved:
    ok = doc.save('竖向收纳盒分步自动保存')
else:
    existing = [f.name for f in folder.dataFiles if f.name == name]
    if existing:
        raise RuntimeError('Default Project 已存在同名新版文件，停止以避免覆盖')
    ok = doc.saveAs(name, folder, '300×210×210 mm 竖向插拔 PLA FDM 收纳盒', '')
if not ok or not doc.isSaved:
    raise RuntimeError('Fusion 原生文档保存失败')
print({'saved': doc.isSaved, 'document_name': doc.name,
       'project': project.name, 'hub': hub.name})
