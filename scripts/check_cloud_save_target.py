app = adsk.core.Application.get()
hub = app.data.dataHubs.item(0)
project = next(p for p in hub.dataProjects if p.name == 'Default Project')
folder = project.rootFolder
print({'hub': hub.name, 'project': project.name, 'folder': folder.name,
       'same_name_files': [f.name for f in folder.dataFiles if f.name == 'Mac mini 便携收纳盒']})
