design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_外框壳体')
if body is None:
    raise RuntimeError('找不到外框壳体')

sketch = root.sketches.add(root.xYConstructionPlane)
sketch.name = '03_底部横向格栅轮廓_缝4mm'
y_positions = []
y = 4.4
while y + 4.0 <= 255.6:
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(4.4 / 10, y / 10, 0),
        adsk.core.Point3D.create(385.6 / 10, (y + 4.0) / 10, 0)
    )
    y_positions.append(y)
    y += 6.2

profiles = adsk.core.ObjectCollection.create()
for profile in sketch.profiles:
    profiles.add(profile)
if profiles.count == 0:
    raise RuntimeError('格栅轮廓创建失败')

before_volume = body.volume
extrude_input = root.features.extrudeFeatures.createInput(
    profiles, adsk.fusion.FeatureOperations.CutFeatureOperation
)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('WallT')
)
if not extrude_input.setOneSideExtent(
    extent, adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
):
    raise RuntimeError('格栅切除深度设置失败')
feature = root.features.extrudeFeatures.add(extrude_input)
feature.name = '03_底部格栅_缝4筋2.2'

after_volume = body.volume
expected_delta = profiles.count * 38.12 * 0.4 * 0.22
actual_delta = before_volume - after_volume
if abs(actual_delta - expected_delta) > 0.2:
    raise RuntimeError(
        f'格栅切除体积异常: 实际 {actual_delta:.3f} cm^3, 预期 {expected_delta:.3f} cm^3'
    )
print({'step': 3, 'slot_count': profiles.count,
       'slot_width_mm': 4.0, 'rib_width_mm': 2.2,
       'slot_length_mm': 381.2, 'cut_depth_mm': 2.2,
       'volume_delta_cm3': actual_delta,
       'body_count': root.bRepBodies.count,
       'feature_name': feature.name})
