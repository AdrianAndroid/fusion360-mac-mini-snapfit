design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_外框壳体')
for side in ['左', '右']:
    feature = root.features.extrudeFeatures.itemByName(f'05_{side}拎带孔_Ø9mm')
    if feature is None:
        raise RuntimeError(f'找不到{side}侧拎带孔特征')
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('WallT')
    )
    feature.timelineObject.rollTo(True)
    if not feature.setOneSideExtent(
        extent, adsk.fusion.ExtentDirections.NegativeExtentDirection,
        adsk.core.ValueInput.createByString('0 deg')
    ):
        raise RuntimeError(f'{side}侧拎带孔深度修正失败')
    design.timeline.moveToEnd()

expected_boss = math.pi * (0.9 ** 2 - 0.45 ** 2) * 0.45
expected_hole = math.pi * 0.45 ** 2 * 0.22
expected_final = 368.22752458177055 + 2 * (expected_boss - expected_hole)
if abs(body.volume - expected_final) > 0.001:
    raise RuntimeError(
        f'步骤5修正后总体积异常: 实际 {body.volume:.6f}, 预期 {expected_final:.6f} cm^3'
    )
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤5修正后实体数量不为1')
print({'step': 5, 'corrected_hole_depth_mm': 2.2,
       'actual_volume_cm3': body.volume, 'expected_volume_cm3': expected_final,
       'body_count': root.bRepBodies.count,
       'features': [f.name for f in root.features.extrudeFeatures if f.name.startswith('05_')]})
