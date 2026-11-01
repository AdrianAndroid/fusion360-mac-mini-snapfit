design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
if root.bRepBodies.count != 2:
    raise RuntimeError('步骤3要求当前仅有底座和左侧板')
base = next(body for body in root.bRepBodies if body.name == '01_底座总成')
left = next(body for body in root.bRepBodies if body.name == '02_左侧板')
volumes_before = {base.name: base.physicalProperties.volume, left.name: left.physicalProperties.volume}
# 保护既有实体，避免多实体切除影响底座或左板。
base.isVisible = False
left.isVisible = False


def offset_yz(x, name):
    plane_input = root.constructionPlanes.createInput()
    plane_input.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByString(f'{x} mm'))
    plane = root.constructionPlanes.add(plane_input)
    plane.name = name
    if abs(plane.geometry.origin.x*10-x) > 0.001:
        raise RuntimeError(name + '位置异常')
    return plane


def world_to_sketch(sketch, point):
    inverse = sketch.transform.copy()
    if not inverse.invert():
        raise RuntimeError('草图逆变换失败')
    point.transformBy(inverse)
    return point


def world_rect(sketch, x, y1, z1, y2, z2):
    points = [(y1, z1), (y2, z1), (y2, z2), (y1, z2)]
    local = [world_to_sketch(sketch, adsk.core.Point3D.create(x/10, y/10, z/10)) for y, z in points]
    for index in range(4):
        sketch.sketchCurves.sketchLines.addByTwoPoints(local[index], local[(index+1) % 4])


def world_circle(sketch, x, y, z, radius):
    center = world_to_sketch(sketch, adsk.core.Point3D.create(x/10, y/10, z/10))
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius/10)


def profiles_of(sketch):
    profiles = adsk.core.ObjectCollection.create()
    for profile in sketch.profiles:
        profiles.add(profile)
    return profiles


def one_side(name, sketch, distance, positive_x, operation, target=None):
    feature_input = root.features.extrudeFeatures.createInput(profiles_of(sketch), operation)
    if target is not None:
        targets = adsk.core.ObjectCollection.create()
        targets.add(target)
        feature_input.targetBodies = targets
    _, _, _, normal = sketch.transform.getAsCoordinateSystem()
    is_positive = normal.x > 0 if positive_x else normal.x < 0
    feature_input.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')),
        adsk.fusion.ExtentDirections.PositiveExtentDirection if is_positive else adsk.fusion.ExtentDirections.NegativeExtentDirection,
        adsk.core.ValueInput.createByString('0 deg'))
    feature = root.features.extrudeFeatures.add(feature_input)
    feature.name = name
    return feature


def through_cut(name, sketch, target, distance=3.0):
    feature_input = root.features.extrudeFeatures.createInput(
        profiles_of(sketch), adsk.fusion.FeatureOperations.CutFeatureOperation)
    targets = adsk.core.ObjectCollection.create()
    targets.add(target)
    feature_input.targetBodies = targets
    feature_input.setTwoSidesExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')),
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')))
    feature = root.features.extrudeFeatures.add(feature_input)
    feature.name = name
    return feature


main_plane = offset_yz(297.8, '03_右侧板内表面平面_X297.8mm')
sketch = root.sketches.add(main_plane)
sketch.name = '03_右侧板外轮廓草图_210x210mm'
world_rect(sketch, 297.8, 0, 0, 210, 210)
one_side('03_右侧板基体_厚2.2mm', sketch, 2.2, True,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
if root.bRepBodies.count != 3:
    raise RuntimeError('右侧板未形成独立实体')
right = next(body for body in root.bRepBodies
             if body.entityToken not in (base.entityToken, left.entityToken))
right.name = '03_右侧板'

outer_edges = adsk.core.ObjectCollection.create()
for edge in right.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    dz = (box.maxPoint.z-box.minPoint.z)*10
    cy = (box.minPoint.y+box.maxPoint.y)*5
    cz = (box.minPoint.z+box.maxPoint.z)*5
    if (abs(dx-2.2) < 0.01 and dy < 0.01 and dz < 0.01
            and any(abs(cy-y) < 0.01 for y in (0, 210))
            and any(abs(cz-z) < 0.01 for z in (0, 210))):
        outer_edges.add(edge)
if outer_edges.count != 4:
    raise RuntimeError(f'右侧板外轮廓边数量异常: {outer_edges.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    outer_edges, adsk.core.ValueInput.createByString('OuterR'), False)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '03_右侧板外轮廓_R3'

side_y = [(24, 36), (99, 111), (174, 186)]
rear_z = [(24, 36), (99, 111), (174, 186)]
sketch = root.sketches.add(main_plane)
sketch.name = '03_右侧板六个贯通母槽草图_单边间隙0.2mm'
for y1, y2 in side_y:
    world_rect(sketch, 297.8, y1-0.2, -0.2, y2+0.2, 2.4)
for z1, z2 in rear_z:
    world_rect(sketch, 297.8, 207.6, z1-0.2, 210.2, z2+0.2)
through_cut('03_右侧板母槽_底3后3_单边0.2mm', sketch, right)

# 内侧向壳体方向1.2范围的R1榫根让位。
sketch = root.sketches.add(main_plane)
sketch.name = '03_右侧板R1榫根让位草图'
for y1, y2 in side_y:
    world_rect(sketch, 297.8, y1-1.2, -0.2, y2+1.2, 2.4)
for z1, z2 in rear_z:
    world_rect(sketch, 297.8, 207.6, z1-1.2, 210.2, z2+1.2)
one_side('03_右侧板R1榫根让位_深1.2mm', sketch, 1.2, True,
         adsk.fusion.FeatureOperations.CutFeatureOperation, right)

# 右侧Ø18凸台向外4.5，向内搭接0.1。
boss_plane = offset_yz(299.9, '03_右侧拎带凸台搭接平面_X299.9mm')
sketch = root.sketches.add(boss_plane)
sketch.name = '03_右侧拎带凸台草图_R9'
world_circle(sketch, 299.9, 105, 105, 9)
one_side('03_右侧拎带凸台_外厚4.5mm', sketch, 4.6, True,
         adsk.fusion.FeatureOperations.JoinFeatureOperation)

sketch = root.sketches.add(main_plane)
sketch.name = '03_右侧拎带孔草图_D9'
world_circle(sketch, 297.8, 105, 105, 4.5)
through_cut('03_右侧拎带孔_D9', sketch, right, 8.0)

base.isVisible = True
left.isVisible = True
for body in (base, left):
    if abs(body.physicalProperties.volume-volumes_before[body.name]) > 0.000001:
        raise RuntimeError('右侧板建模误改了既有实体: ' + body.name)
if root.bRepBodies.count != 3:
    raise RuntimeError('步骤3完成后实体数量不是3')
non_manifold = {body.name: sum(1 for edge in body.edges if edge.faces.count > 2)
                for body in root.bRepBodies}
if any(non_manifold.values()):
    raise RuntimeError(f'存在非流形边: {non_manifold}')
box = right.boundingBox
print({'step': 3, 'bodies': [body.name for body in root.bRepBodies],
       'existing_volumes_unchanged': True, 'non_manifold': non_manifold,
       'right_outer_R3_edges': outer_edges.count,
       'base_mortise_count': 3, 'rear_interlock_mortise_count': 3,
       'mortise_width_mm': 12.4, 'single_side_clearance_mm': 0.2,
       'root_relief_depth_mm': 1.2,
       'handle_hole_diameter_mm': 9.0, 'boss_outer_diameter_mm': 18.0,
       'boss_outward_thickness_mm': 4.5,
       'right_bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                         'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
