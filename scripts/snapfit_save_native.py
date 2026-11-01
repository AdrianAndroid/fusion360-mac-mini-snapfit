app = adsk.core.Application.get()
doc = app.activeDocument
name = 'Mac mini 收纳盒_无螺丝卯榫卡扣_300x210x210'
hub = next(h for h in app.data.dataHubs if h.name == 'zhaojian')
project = next(p for p in hub.dataProjects if p.name == 'Default Project')
folder = project.rootFolder
if doc.name == name and doc.dataFile:
    ok = doc.save('无螺丝卯榫卡扣四件式分步保存')
else:
    existing = [f.name for f in folder.dataFiles if f.name == name]
    if existing:
        raise RuntimeError('Default Project 已存在同名卡扣版文件，停止以避免覆盖')
    ok = doc.saveAs(name, folder, '四件式纯卡扣 PLA FDM 收纳盒；榫卯单边间隙0.2mm', '')
if not ok:
    raise RuntimeError('原生文档保存失败')
print({'saved': doc.isSaved, 'document_name': doc.name,
       'project': project.name, 'hub': hub.name})
