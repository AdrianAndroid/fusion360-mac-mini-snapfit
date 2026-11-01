design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
sketch = root.sketches.itemByName('04_草图_Mac左侧散热窗_边框8mm')
plane = root.yZConstructionPlane.geometry
origin = plane.origin
normal = plane.normal
x_axis = None
y_axis = None
points = []
for point in sketch.sketchPoints:
    p = point.worldGeometry
    points.append([round(p.x*10, 4), round(p.y*10, 4), round(p.z*10, 4)])
print({'plane_origin_mm': [origin.x*10, origin.y*10, origin.z*10],
       'plane_normal': [normal.x, normal.y, normal.z],
       'plane_primary_axis': 'use worldGeometry points',
       'plane_secondary_axis': 'use worldGeometry points',
       'sketch_world_points_mm': points,
       'profile_count': sketch.profiles.count,
       'body_bbox_mm': [root.bRepBodies.item(0).boundingBox.minPoint.x*10,
                        root.bRepBodies.item(0).boundingBox.maxPoint.x*10]})
