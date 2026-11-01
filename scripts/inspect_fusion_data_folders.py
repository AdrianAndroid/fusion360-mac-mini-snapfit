app = adsk.core.Application.get()
data = app.data
hubs = []
for hub in data.dataHubs:
    projects = []
    for project in hub.dataProjects:
        projects.append({'name': project.name, 'root_folder': project.rootFolder.name})
    hubs.append({'name': hub.name, 'projects': projects})
print({'hub_count': data.dataHubs.count, 'hubs': hubs})
