design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
sketch = design.rootComponent.sketches.itemByName('04_后部出线槽轮廓_宽10mm')
if sketch is None:
    raise RuntimeError('找不到步骤4诊断草图')
for i in range(sketch.profiles.count):
    profile = sketch.profiles.item(i)
    box = profile.boundingBox
    print({'index': i, 'loop_count': profile.profileLoops.count,
           'bbox': [[box.minPoint.x, box.minPoint.y, box.minPoint.z],
                    [box.maxPoint.x, box.maxPoint.y, box.maxPoint.z]]})
