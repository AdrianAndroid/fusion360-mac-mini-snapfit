design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
print({'bodies': [
    {'name': b.name, 'volume_cm3': b.volume,
     'bbox_mm': [[v * 10 for v in (b.boundingBox.minPoint.x, b.boundingBox.minPoint.y, b.boundingBox.minPoint.z)],
                 [v * 10 for v in (b.boundingBox.maxPoint.x, b.boundingBox.maxPoint.y, b.boundingBox.maxPoint.z)]]}
    for b in root.bRepBodies
], 'sketches': [s.name for s in root.sketches],
   'extrudes': [f.name for f in root.features.extrudeFeatures],
   'timeline_count': design.timeline.count,
   'timeline_last': [design.timeline.item(i).entity.name for i in range(max(0, design.timeline.count - 5), design.timeline.count)]})
