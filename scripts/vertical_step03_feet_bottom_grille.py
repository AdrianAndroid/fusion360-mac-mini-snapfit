design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤3要求新版壳体与隔板为单一实体')
if root.features.extrudeFeatures.itemByName('03_支撑脚_高5mm_壁厚2.2mm'):
    raise RuntimeError('步骤3支撑脚已存在，停止以避免重复建模')


def set_parameter(name, expression):
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expression), 'mm', name)


for name, expression in {
    'FootH': '5 mm', 'FootWallT': '2.2 mm', 'FootJoinOverlap': '0.1 mm',
    'BottomSlotW': '4 mm', 'BottomRibW': '2.2 mm',
}.items():
    set_parameter(name, expression)

# 顶面向上搭接0.1mm，错开隔板在Z=0的接缝；外部可见抬高仍为5mm。
plane_input = root.constructionPlanes.createInput()
plane_input.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByString('FootJoinOverlap'))
plane = root.constructionPlanes.add(plane_input)
plane.name = '03_支撑脚搭接平面_壳底上0.1mm'
foot_sketch = root.sketches.add(plane)
foot_sketch.name = '03_草图_支撑脚环形截面_壁厚2.2mm'
foot_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(30, 21, 0))
foot_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0.22, 0.22, 0), adsk.core.Point3D.create(29.78, 20.78, 0))
ring_profiles = [p for p in foot_sketch.profiles if p.profileLoops.count == 2]
if len(ring_profiles) != 1:
    raise RuntimeError(f'支撑脚环形轮廓数量异常: {len(ring_profiles)}')
foot_input = root.features.extrudeFeatures.createInput(
    ring_profiles[0], adsk.fusion.FeatureOperations.JoinFeatureOperation)
foot_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('FootH + FootJoinOverlap')),
    adsk.fusion.ExtentDirections.NegativeExtentDirection,
    adsk.core.ValueInput.createByString('0 deg'))
foot = root.features.extrudeFeatures.add(foot_input)
foot.name = '03_支撑脚_高5mm_壁厚2.2mm'
if root.bRepBodies.count != 1:
    raise RuntimeError('支撑脚未与壳体合并为单一实体')

outer_edges = adsk.core.ObjectCollection.create()
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x - box.minPoint.x) * 10
    dy = (box.maxPoint.y - box.minPoint.y) * 10
    dz = (box.maxPoint.z - box.minPoint.z) * 10
    cx = (box.minPoint.x + box.maxPoint.x) * 5
    cy = (box.minPoint.y + box.maxPoint.y) * 5
    if (dx < 0.01 and dy < 0.01 and abs(dz - 5.1) < 0.01
            and abs(box.minPoint.z * 10 + 5.0) < 0.01
            and any(abs(cx - x) < 0.01 for x in (0, 300))
            and any(abs(cy - y) < 0.01 for y in (0, 210))):
        outer_edges.add(edge)
if outer_edges.count != 4:
    raise RuntimeError(f'支撑脚外竖角数量异常: {outer_edges.count}，预期4')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    outer_edges, adsk.core.ValueInput.createByString('OuterR'), False)
foot_corners = root.features.filletFeatures.add(fillet_input)
foot_corners.name = '03_支撑脚外竖角_R3'
if any(edge.faces.count > 2 for edge in body.edges):
    raise RuntimeError('支撑脚完成后检测到非流形边，停止格栅切除')

# 周边脚壁不属于隔板/格栅筋，不添加无法生成的根部R2。
grille_sketch = root.sketches.add(root.xYConstructionPlane)
grille_sketch.name = '03_草图_底部横向格栅_缝4mm_筋2.2mm'
slot_count = 32
pitch = 6.2
occupied = slot_count * 4.0 + (slot_count - 1) * 2.2
y_start = 4.4 + ((205.6 - 4.4) - occupied) / 2
for index in range(slot_count):
    y1 = y_start + index * pitch
    grille_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.44, y1 / 10, 0),
        adsk.core.Point3D.create(29.56, (y1 + 4.0) / 10, 0))
profiles = adsk.core.ObjectCollection.create()
for profile in grille_sketch.profiles:
    profiles.add(profile)
if profiles.count != slot_count:
    raise RuntimeError(f'底部格栅轮廓数量异常: {profiles.count}')
grille_input = root.features.extrudeFeatures.createInput(
    profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
grille_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg'))
grille = root.features.extrudeFeatures.add(grille_input)
grille.name = '03_底部横向格栅_32缝4mm_筋2.2mm'

box = body.boundingBox
size_mm = [(box.maxPoint.x-box.minPoint.x)*10,
           (box.maxPoint.y-box.minPoint.y)*10,
           (box.maxPoint.z-box.minPoint.z)*10]
non_manifold_count = sum(1 for edge in body.edges if edge.faces.count > 2)
if abs(box.minPoint.z*10 + 5.0) > 0.01 or abs(box.maxPoint.z*10 - 210.0) > 0.01:
    raise RuntimeError('步骤3 Z向包围盒异常')
if abs(size_mm[0]-300) > 0.01 or abs(size_mm[1]-210) > 0.01:
    raise RuntimeError('步骤3外轮廓尺寸异常')
if root.bRepBodies.count != 1 or non_manifold_count:
    raise RuntimeError('步骤3完成后存在多实体或非流形边')
print({'step': 3, 'body_count': 1, 'non_manifold_edge_count': non_manifold_count,
       'bbox_size_mm': size_mm, 'visible_foot_height_mm': 5.0,
       'join_overlap_mm': 0.1, 'foot_wall_mm': 2.2,
       'slot_count': slot_count, 'slot_width_mm': 4.0,
       'rib_width_mm': 2.2, 'pitch_mm': pitch,
       'first_slot_y_mm': y_start, 'last_slot_end_y_mm': y_start+31*pitch+4.0,
       'features': [foot.name, foot_corners.name, grille.name]})
