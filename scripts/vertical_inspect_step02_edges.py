design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
body = design.rootComponent.bRepBodies.itemByName('01_竖向收纳盒壳体')
items = []
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    if abs(box.minPoint.z - 0.22) > 0.001 or abs(box.maxPoint.z - 0.22) > 0.001:
        continue
    dx = (box.maxPoint.x - box.minPoint.x) * 10
    dy = (box.maxPoint.y - box.minPoint.y) * 10
    cx = (box.minPoint.x + box.maxPoint.x) * 5
    cy = (box.minPoint.y + box.maxPoint.y) * 5
    items.append({'cx': round(cx, 4), 'cy': round(cy, 4),
                  'dx': round(dx, 4), 'dy': round(dy, 4)})
print({'edge_count': len(items), 'edges': items,
       'features': [f.name for f in design.rootComponent.features.extrudeFeatures]})
