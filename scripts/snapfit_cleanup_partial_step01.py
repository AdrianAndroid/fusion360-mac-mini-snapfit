design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
for name in ['01_底座三边公榫_9个_厚2.2深6mm', '01_底板_壁厚2.2mm']:
    feature = next((f for f in root.features.extrudeFeatures if f.name == name), None)
    if feature:
        feature.deleteMe()
for name in ['01_左右榫15度倒扣草图_1']:
    sketch = next((s for s in root.sketches if s.name == name), None)
    if sketch:
        sketch.deleteMe()
for name in ['01_侧榫倒扣平面_1']:
    plane = next((p for p in root.constructionPlanes if p.name == name), None)
    if plane:
        plane.deleteMe()
print({'partial_step01_removed': True, 'body_count': root.bRepBodies.count,
       'sketch_count': root.sketches.count, 'timeline_count': design.timeline.count})
