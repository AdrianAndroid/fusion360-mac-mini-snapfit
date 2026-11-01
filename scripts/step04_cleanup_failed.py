design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
feature = root.features.extrudeFeatures.itemByName('拉伸11')
if feature is None:
    feature = root.features.extrudeFeatures.itemByName('04_顶部后边缘出线槽_10mm')
if feature:
    feature.deleteMe()
sketch = root.sketches.itemByName('04_后部出线槽轮廓_宽10mm')
if sketch:
    sketch.deleteMe()
print({'body_count': root.bRepBodies.count,
       'volumes_cm3': [b.volume for b in root.bRepBodies],
       'extrudes': [f.name for f in root.features.extrudeFeatures],
       'has_failed_sketch': root.sketches.itemByName('04_后部出线槽轮廓_宽10mm') is not None})
