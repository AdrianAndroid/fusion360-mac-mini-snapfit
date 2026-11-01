design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_外框壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤6要求当前只有外框壳体单一实体')

for name, expression in [
    ('MacVentW', 'MacSlotL - 2 * VentMargin'),
    ('MacVentH', 'OuterH - 2 * VentMargin'),
]:
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(
            name, adsk.core.ValueInput.createByString(expression), 'mm', name
        )

front_faces = []
for face in body.faces:
    plane = adsk.core.Plane.cast(face.geometry)
    if (plane and plane.normal.y < -0.999 and
            abs(face.boundingBox.minPoint.y) < 0.001 and
            abs(face.boundingBox.maxPoint.y) < 0.001):
        front_faces.append(face)
if len(front_faces) != 1:
    raise RuntimeError(f'Mac前壁外侧面数量异常: {len(front_faces)}')

sketch = root.sketches.add(front_faces[0])
sketch.name = '06_Mac散热开窗轮廓_周边8mm'


def sketch_point(x_mm, z_mm):
    return sketch.modelToSketchSpace(
        adsk.core.Point3D.create(x_mm / 10, 0.0, z_mm / 10)
    )


lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    sketch_point(10.2, 8.0), sketch_point(192.65, 62.0)
)
width_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(0).startSketchPoint, lines.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    sketch_point(101.425, 66.0)
)
width_dim.parameter.expression = 'MacVentW'
height_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(1).startSketchPoint, lines.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    sketch_point(197.0, 35.0)
)
height_dim.parameter.expression = 'MacVentH'


def profile_xy_size(profile):
    box = profile.boundingBox
    return (box.maxPoint.x - box.minPoint.x,
            box.maxPoint.y - box.minPoint.y)


window_profiles = []
for profile in sketch.profiles:
    size_x, size_y = profile_xy_size(profile)
    if abs(size_x - 18.245) < 0.001 and abs(size_y - 5.4) < 0.001:
        window_profiles.append(profile)
if len(window_profiles) != 1:
    raise RuntimeError(f'Mac开窗轮廓数量异常: {len(window_profiles)}')

before_cut = body.volume
cut_input = root.features.extrudeFeatures.createInput(
    window_profiles[0], adsk.fusion.FeatureOperations.CutFeatureOperation
)
cut_extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('WallT')
)
if not cut_input.setOneSideExtent(
    cut_extent, adsk.fusion.ExtentDirections.NegativeExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
):
    raise RuntimeError('Mac开窗切除范围设置失败')
cut = root.features.extrudeFeatures.add(cut_input)
cut.name = '06_Mac外侧散热开窗_周边8mm'
cut_delta = before_cut - body.volume
expected_cut = 18.245 * 5.4 * 0.22
if abs(cut_delta - expected_cut) > 0.005:
    raise RuntimeError(
        f'Mac开窗切除体积异常: 实际 {cut_delta:.6f}, 预期 {expected_cut:.6f} cm^3'
    )

# 选择窗口四个贯穿壁厚的角边，按参考图形成大圆角开窗。
corner_edges = adsk.core.ObjectCollection.create()
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = box.maxPoint.x - box.minPoint.x
    dy = box.maxPoint.y - box.minPoint.y
    dz = box.maxPoint.z - box.minPoint.z
    if dx > 0.001 or dz > 0.001 or abs(dy - 0.22) > 0.001:
        continue
    cx = (box.minPoint.x + box.maxPoint.x) / 2
    cz = (box.minPoint.z + box.maxPoint.z) / 2
    if ((abs(cx - 1.02) < 0.001 or abs(cx - 19.265) < 0.001) and
            (abs(cz - 0.8) < 0.001 or abs(cz - 6.2) < 0.001)):
        corner_edges.add(edge)
if corner_edges.count != 4:
    raise RuntimeError(f'Mac开窗角边数量异常: {corner_edges.count}')

before_fillet = body.volume
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    corner_edges, adsk.core.ValueInput.createByString('VentMargin'), False
)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '06_Mac散热开窗圆角_R8'
fillet_delta = body.volume - before_fillet
expected_restore = (4.0 - math.pi) * 0.8 ** 2 * 0.22
if abs(fillet_delta - expected_restore) > 0.005:
    raise RuntimeError(
        f'Mac开窗圆角体积变化异常: 实际 {fillet_delta:.6f}, 预期 {expected_restore:.6f} cm^3'
    )
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤6完成后实体数量不为1')
print({'step': 6, 'window_width_mm': 182.45, 'window_height_mm': 54.0,
       'corner_radius_mm': 8.0, 'margin_mm': 8.0,
       'cut_volume_cm3': cut_delta, 'fillet_volume_restore_cm3': fillet_delta,
       'final_volume_cm3': body.volume, 'body_count': root.bRepBodies.count,
       'features': [cut.name, fillet.name]})
