design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_外框壳体')
if body is None:
    raise RuntimeError('找不到外框壳体')

# 清理仅用于诊断、尚未产生拉伸的旧草图。
existing_sketch = root.sketches.itemByName('04_后部出线槽轮廓_宽10mm')
if existing_sketch:
    existing_sketch.deleteMe()

# 后壁外侧面：Y=260 mm，法线朝 +Y。
rear_faces = []
for face in body.faces:
    plane = adsk.core.Plane.cast(face.geometry)
    if plane and plane.normal.y > 0.999 and abs(face.boundingBox.minPoint.y - 26.0) < 0.001:
        rear_faces.append(face)
if len(rear_faces) != 1:
    raise RuntimeError(f'后壁外侧面数量异常: {len(rear_faces)}')

sketch = root.sketches.add(rear_faces[0])
sketch.name = '04_后部出线槽轮廓_宽10mm'

# 出线槽位于背部走线区中央，X=341.25..351.25 mm，Z=60..70 mm。
def sketch_point(x_mm, z_mm):
    return sketch.modelToSketchSpace(
        adsk.core.Point3D.create(x_mm / 10, 26.0, z_mm / 10)
    )

lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    sketch_point(341.25, 60.0), sketch_point(351.25, 70.0)
)
# 尺寸驱动槽宽及顶面向下的切入深度。
width_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(0).startSketchPoint, lines.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    sketch_point(346.25, 73.0)
)
width_dim.parameter.expression = 'CableSlotW'
height_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(1).startSketchPoint, lines.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    sketch_point(355.0, 65.0)
)
height_dim.parameter.expression = 'CableSlotW'

before_volume = body.volume
# 面上草图同时识别出外边界与槽轮廓，用包围盒明确选取目标小轮廓。
def profile_xy_area(profile):
    box = profile.boundingBox
    return (box.maxPoint.x - box.minPoint.x) * (box.maxPoint.y - box.minPoint.y)

slot_profile = min(sketch.profiles, key=profile_xy_area)
slot_box = slot_profile.boundingBox
# Profile.boundingBox 使用草图局部坐标；后壁草图 X 轴朝向全局 -X。
if (abs(slot_box.minPoint.x + 35.125) > 0.001 or
        abs(slot_box.maxPoint.x + 34.125) > 0.001 or
        abs(slot_box.minPoint.y - 6.0) > 0.001 or
        abs(slot_box.maxPoint.y - 7.0) > 0.001):
    raise RuntimeError('出线槽目标轮廓位置异常')
extrude_input = root.features.extrudeFeatures.createInput(
    slot_profile, adsk.fusion.FeatureOperations.CutFeatureOperation
)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('WallT')
)
if not extrude_input.setOneSideExtent(
    extent, adsk.fusion.ExtentDirections.NegativeExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
):
    raise RuntimeError('出线槽切除范围设置失败')
feature = root.features.extrudeFeatures.add(extrude_input)
feature.name = '04_顶部后边缘出线槽_10mm'

actual_delta = before_volume - body.volume
expected_delta = 1.0 * 1.0 * 0.22
if abs(actual_delta - expected_delta) > 0.001:
    raise RuntimeError(
        f'出线槽切除体积异常: 实际 {actual_delta:.6f}, 预期 {expected_delta:.6f} cm^3'
    )
print({'step': 4, 'slot_width_mm': 10.0, 'slot_drop_mm': 10.0,
       'slot_center_x_mm': 346.25, 'rear_wall_y_mm': [257.8, 260.0],
       'volume_delta_cm3': actual_delta, 'body_count': root.bRepBodies.count,
       'feature_name': feature.name})
