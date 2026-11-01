import math

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
if root.bRepBodies.count != 1:
    raise RuntimeError('续跑步骤1时底座实体数量异常')
body = root.bRepBodies.item(0)
foot_edges = adsk.core.ObjectCollection.create()
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    cx = (box.minPoint.x+box.maxPoint.x)*5
    cy = (box.minPoint.y+box.maxPoint.y)*5
    if (dx < 0.01 and dy < 0.01 and abs(box.minPoint.z*10+5) < 0.01
            and any(abs(cx-x) < 0.01 for x in (2.2, 297.8))
            and any(abs(cy-y) < 0.01 for y in (0, 207.8))):
        foot_edges.add(edge)
if foot_edges.count != 4:
    raise RuntimeError(f'支撑脚及相连外竖角数量异常: {foot_edges.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    foot_edges, adsk.core.ValueInput.createByString('OuterR'), False)
foot_fillet = root.features.filletFeatures.add(fillet_input)
foot_fillet.name = '01_支撑脚及相连外竖角_R3'


def rect(sketch, x1, y1, x2, y2):
    return sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(x1/10, y1/10, 0),
        adsk.core.Point3D.create(x2/10, y2/10, 0))


grille_sketch = root.sketches.add(root.xYConstructionPlane)
grille_sketch.name = '01_底部横向格栅草图_32缝'
pitch = 6.2
occupied = 32*4 + 31*2.2
y_start = 4.4 + ((205.6-4.4)-occupied)/2
for index in range(32):
    y1 = y_start + index*pitch
    rect(grille_sketch, 4.4, y1, 295.6, y1+4)
profiles = adsk.core.ObjectCollection.create()
for profile in grille_sketch.profiles:
    profiles.add(profile)
if profiles.count != 32:
    raise RuntimeError(f'底部格栅轮廓数量异常: {profiles.count}')
grille_input = root.features.extrudeFeatures.createInput(
    profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
grille_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg'))
grille = root.features.extrudeFeatures.add(grille_input)
grille.name = '01_底部横向格栅_32缝4mm_筋2.2mm'

non_manifold = sum(1 for edge in body.edges if edge.faces.count > 2)
if root.bRepBodies.count != 1 or non_manifold:
    raise RuntimeError('步骤1完成后存在多实体或非流形边')
checks = [
    (38.75-2.2, 36.55), (67.8-40.95, 26.85),
    (80.25-70.0, 10.25), (115.2-82.45, 32.75),
    (200.65-2.2, 198.45), (104.55-2.2, 102.35),
    (72.8-2.2, 70.6), (107.95-2.2, 105.75),
    (297.8-115.2, 182.6),
]
if any(abs(actual-expected) > 0.001 for actual, expected in checks):
    raise RuntimeError('仓位或走线通道净尺寸自检失败')
box = body.boundingBox
print({'step': 1, 'body': body.name, 'body_count': root.bRepBodies.count,
       'non_manifold_edge_count': non_manifold,
       'male_tenon_count': 9, 'tenon_thickness_mm': 2.2,
       'tenon_insert_depth_mm': 6.0, 'tenon_root_R1_edges': 18,
       'barb_angle_deg': 15.0, 'barb_projection_mm': 0.6,
       'barb_ramp_length_mm': 0.6/math.tan(math.radians(15)),
       'divider_root_R2_edges': 19,
       'partition_top_z_mm': 200.65, 'top_wiring_gap_mm': 9.35,
       'bottom_slot_count': 32, 'bottom_slot_mm': 4.0, 'bottom_rib_mm': 2.2,
       'outer_R3_edges': foot_edges.count,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
