app = adsk.core.Application.get()
doc = app.activeDocument
name = 'Mac mini 收纳盒_顶面敞开_卯榫卡扣_300x210x210'
hub = next(h for h in app.data.dataHubs if h.name == 'zhaojian')
project = next(p for p in hub.dataProjects if p.name == 'Default Project')
folder = project.rootFolder
if doc.name == name and doc.dataFile:
    ok = doc.save('顶面敞开四件式卯榫卡扣分步保存')
else:
    existing = [f.name for f in folder.dataFiles if f.name == name]
    if existing:
        raise RuntimeError('Default Project 已存在同名顶面敞开文件，停止以避免覆盖')
    ok = doc.saveAs(name, folder, '顶面敞开；设备从上向下竖插；四件式纯卡扣PLA FDM', '')
if not ok:
    raise RuntimeError('原生文档保存失败')
print({'saved': doc.isSaved, 'document_name': doc.name,
       'project': project.name, 'hub': hub.name})
