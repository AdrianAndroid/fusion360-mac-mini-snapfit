design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
base = root.features.extrudeFeatures.itemByName('01_外框基体_高70mm')
if base is None:
    raise RuntimeError('找不到步骤1外框基体特征')
base.timelineObject.rollTo(True)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('OuterH')
)
if not base.setOneSideExtent(
    extent,
    adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
):
    raise RuntimeError('外框基体单侧拉伸修正失败')
design.timeline.moveToEnd()
body = root.bRepBodies.itemByName('01_外框壳体')
bbox = body.boundingBox
size_mm = [
    (bbox.maxPoint.x - bbox.minPoint.x) * 10,
    (bbox.maxPoint.y - bbox.minPoint.y) * 10,
    (bbox.maxPoint.z - bbox.minPoint.z) * 10,
]
if any(abs(a - b) > 0.01 for a, b in zip(size_mm, [390, 260, 70])):
    raise RuntimeError(f'外框尺寸仍异常: {size_mm}')
if abs(bbox.minPoint.z) > 0.0001:
    raise RuntimeError(f'外框底面未位于 Z=0: {bbox.minPoint.z}')
print({'step': 1, 'corrected': True, 'size_mm': size_mm,
       'z_min_mm': bbox.minPoint.z * 10, 'z_max_mm': bbox.maxPoint.z * 10,
       'body_count': root.bRepBodies.count})
