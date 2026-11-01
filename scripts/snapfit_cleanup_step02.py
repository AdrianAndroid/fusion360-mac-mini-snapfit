design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
removed = []
for item in reversed(list(design.timeline)):
    entity = item.entity
    if entity and entity.isValid and entity.name.startswith('02_'):
        removed.append(entity.name)
        entity.deleteMe()
for sketch in list(root.sketches):
    if sketch.name.startswith('02_'):
        sketch.deleteMe()
for plane in list(root.constructionPlanes):
    if plane.name.startswith('02_'):
        plane.deleteMe()
for body in root.bRepBodies:
    body.isVisible = True
print({'removed_step02_entities': removed, 'body_count': root.bRepBodies.count,
       'bodies': [{'name': body.name, 'volume_cm3': body.physicalProperties.volume}
                  for body in root.bRepBodies]})
