design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤4要求当前为单一实体')
feature_name = '04_Mac左侧散热窗_194x194mm_边框8mm'
if root.features.extrudeFeatures.itemByName(feature_name):
    raise RuntimeError('Mac左侧散热窗已存在，停止以避免重复切除')
parameter = design.userParameters.itemByName('MacVentBorder')
if parameter is None:
    design.userParameters.add(
        'MacVentBorder', adsk.core.ValueInput.createByString('8 mm'), 'mm',
        'Mac左侧散热窗四周实体边框'
    )
else:
    parameter.expression = '8 mm'

# 读取草图局部到世界矩阵，以逆变换精确放置全局Y/Z=8..202的轮廓。
existing_sketch = root.sketches.itemByName('04_草图_Mac左侧散热窗_边框8mm')
if existing_sketch:
    existing_sketch.deleteMe()
existing_plane = root.constructionPlanes.itemByName('04_Mac左侧外壁草图平面')
if existing_plane:
    existing_plane.deleteMe()
sketch = root.sketches.add(root.yZConstructionPlane)
sketch.name = '04_草图_Mac左侧散热窗_边框8mm'
inverse = sketch.transform.copy()
if not inverse.invert():
    raise RuntimeError('左侧草图坐标逆变换失败')
point_one = adsk.core.Point3D.create(0, 0.8, 0.8)
point_two = adsk.core.Point3D.create(0, 20.2, 20.2)
point_one.transformBy(inverse)
point_two.transformBy(inverse)
sketch.sketchCurves.sketchLines.addTwoPointRectangle(point_one, point_two)
if sketch.profiles.count != 1:
    raise RuntimeError(f'Mac散热窗轮廓数量异常: {sketch.profiles.count}')
cut_input = root.features.extrudeFeatures.createInput(
    sketch.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation
)
cut_input.setTwoSidesExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.core.ValueInput.createByString('0 deg'),
    adsk.core.ValueInput.createByString('0 deg')
)
vent = root.features.extrudeFeatures.add(cut_input)
vent.name = feature_name

# 开口四条内侧壁的范围必须严格为Y/Z=8..202、X=0..2.2。
matched_faces = []
for face in body.faces:
    box = face.boundingBox
    x1, x2 = box.minPoint.x * 10, box.maxPoint.x * 10
    y1, y2 = box.minPoint.y * 10, box.maxPoint.y * 10
    z1, z2 = box.minPoint.z * 10, box.maxPoint.z * 10
    if (abs(x1) < 0.01 and abs(x2 - 2.2) < 0.01
            and ((abs(y1 - 8) < 0.01 and abs(y2 - 8) < 0.01)
                 or (abs(y1 - 202) < 0.01 and abs(y2 - 202) < 0.01)
                 or (abs(z1 - 8) < 0.01 and abs(z2 - 8) < 0.01)
                 or (abs(z1 - 202) < 0.01 and abs(z2 - 202) < 0.01))
            and ((abs(z1 - 8) < 0.01 and abs(z2 - 202) < 0.01)
                 or (abs(y1 - 8) < 0.01 and abs(y2 - 202) < 0.01))):
        matched_faces.append({'x_mm': [x1, x2], 'y_mm': [y1, y2], 'z_mm': [z1, z2]})
non_manifold_count = sum(1 for edge in body.edges if edge.faces.count > 2)
if len(matched_faces) != 4:
    raise RuntimeError(f'Mac散热窗内侧壁数量或边界异常: {matched_faces}')
if root.bRepBodies.count != 1 or non_manifold_count:
    raise RuntimeError('Mac散热窗完成后存在多实体或非流形边')
print({'step': 4, 'opening_yz_mm': [194.0, 194.0],
       'solid_border_mm': 8.0, 'cut_depth_mm': 2.2,
       'opening_bounds_mm': {'y': [8.0, 202.0], 'z': [8.0, 202.0]},
       'opening_side_faces': len(matched_faces),
       'body_count': root.bRepBodies.count,
       'non_manifold_edge_count': non_manifold_count,
       'feature': vent.name})
