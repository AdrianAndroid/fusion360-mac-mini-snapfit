design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
for feature_name in ('03_支撑脚外竖角_R3', '03_支撑脚_高5mm_壁厚2.2mm'):
    feature = root.features.filletFeatures.itemByName(feature_name) or root.features.extrudeFeatures.itemByName(feature_name)
    if feature:
        if not feature.deleteMe():
            raise RuntimeError('无法删除待重建特征: ' + feature_name)
sketch = root.sketches.itemByName('03_草图_支撑脚环形截面_壁厚2.2mm')
if sketch:
    sketch.deleteMe()

plane_input = root.constructionPlanes.createInput()
plane_input.setByOffset(
    root.xYConstructionPlane, adsk.core.ValueInput.createByString('FootJoinOverlap')
)
plane = root.constructionPlanes.add(plane_input)
plane.name = '03_支撑脚搭接平面_壳底上0.1mm'
foot_sketch = root.sketches.add(plane)
foot_sketch.name = '03_草图_支撑脚环形截面_壁厚2.2mm'
foot_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(30, 21, 0)
)
foot_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0.22, 0.22, 0), adsk.core.Point3D.create(29.78, 20.78, 0)
)
ring_profiles = [p for p in foot_sketch.profiles if p.profileLoops.count == 2]
if len(ring_profiles) != 1:
    raise RuntimeError(f'支撑脚环形轮廓数量异常: {len(ring_profiles)}')
foot_input = root.features.extrudeFeatures.createInput(
    ring_profiles[0], adsk.fusion.FeatureOperations.JoinFeatureOperation
)
foot_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('FootH + FootJoinOverlap')
    ),
    adsk.fusion.ExtentDirections.NegativeExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
)
foot = root.features.extrudeFeatures.add(foot_input)
foot.name = '03_支撑脚_高5mm_壁厚2.2mm'
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
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
    raise RuntimeError(f'重建后支撑脚外竖角数量异常: {outer_edges.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    outer_edges, adsk.core.ValueInput.createByString('OuterR'), False
)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '03_支撑脚外竖角_R3'
non_manifold = []
for edge in body.edges:
    if edge.faces.count > 2:
        box = edge.boundingBox
        non_manifold.append({'faces': edge.faces.count,
                             'min_mm': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                             'max_mm': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]})
print({'body_count': root.bRepBodies.count, 'overlap_mm': 0.1,
       'non_manifold_edge_count': len(non_manifold),
       'non_manifold_edges': non_manifold,
       'foot_z_mm': [-5.0, 0.1]})
if root.bRepBodies.count != 1 or non_manifold:
    raise RuntimeError('重建后仍有实体或非流形异常，停止后续特征')
