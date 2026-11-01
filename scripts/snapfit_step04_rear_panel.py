import math

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
if root.bRepBodies.count != 3:
    raise RuntimeError('步骤4要求当前已有底座、左板和右板')
existing = {body.name: body for body in root.bRepBodies}
volumes_before = {name: body.physicalProperties.volume for name, body in existing.items()}
for body in existing.values():
    body.isVisible = False

for name, expression in {
    'RearSlotW': '4 mm', 'RearRibW': '2.2 mm', 'RearCableSlotH': '10 mm',
    'RearGrilleBottomZ': '4.6 mm',
}.items():
    if not design.userParameters.itemByName(name):
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expression), 'mm', name)


def offset_plane(reference, axis, target, name):
    normal = getattr(reference.geometry.normal, axis)
    offset = target/normal
    plane_input = root.constructionPlanes.createInput()
    plane_input.setByOffset(reference, adsk.core.ValueInput.createByString(f'{offset} mm'))
    plane = root.constructionPlanes.add(plane_input)
    plane.name = name
    if abs(getattr(plane.geometry.origin, axis)*10-target) > 0.001:
        raise RuntimeError(name + '位置异常')
    return plane


def world_to_sketch(sketch, point):
    inverse = sketch.transform.copy()
    if not inverse.invert():
        raise RuntimeError('草图逆变换失败')
    point.transformBy(inverse)
    return point


def world_rect_xz(sketch, y, x1, z1, x2, z2):
    points = [(x1, z1), (x2, z1), (x2, z2), (x1, z2)]
    local = [world_to_sketch(sketch, adsk.core.Point3D.create(x/10, y/10, z/10)) for x, z in points]
    for index in range(4):
        sketch.sketchCurves.sketchLines.addByTwoPoints(local[index], local[(index+1) % 4])


def world_polygon_xy(sketch, z, points):
    local = [world_to_sketch(sketch, adsk.core.Point3D.create(x/10, y/10, z/10)) for x, y in points]
    for index in range(len(local)):
        sketch.sketchCurves.sketchLines.addByTwoPoints(local[index], local[(index+1) % len(local)])


def profiles_of(sketch):
    profiles = adsk.core.ObjectCollection.create()
    for profile in sketch.profiles:
        profiles.add(profile)
    return profiles


def one_side(name, sketch, axis, positive, distance, operation, target=None):
    feature_input = root.features.extrudeFeatures.createInput(profiles_of(sketch), operation)
    if target is not None:
        targets = adsk.core.ObjectCollection.create()
        targets.add(target)
        feature_input.targetBodies = targets
    _, _, _, normal = sketch.transform.getAsCoordinateSystem()
    component = getattr(normal, axis)
    is_positive = component > 0 if positive else component < 0
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


main_plane = offset_plane(root.xZConstructionPlane, 'y', 207.8, '04_后盖板前表面平面_Y207.8mm')
sketch = root.sketches.add(main_plane)
sketch.name = '04_后盖板外轮廓草图_295.6x210mm'
world_rect_xz(sketch, 207.8, 2.2, 0, 297.8, 210)
one_side('04_后盖板基体_厚2.2mm', sketch, 'y', True, 2.2,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
if root.bRepBodies.count != 4:
    raise RuntimeError('后盖板未形成独立实体')
rear = next(body for body in root.bRepBodies if body.entityToken not in
            [body.entityToken for body in existing.values()])
rear.name = '04_后盖板'

# 左右各3个互锁小榫，厚2.2、插入6、宽12；根部搭接0.1。
rear_z = [(24, 36), (99, 111), (174, 186)]
sketch = root.sketches.add(main_plane)
sketch.name = '04_后盖板左右互锁小榫草图_6个'
for z1, z2 in rear_z:
    world_rect_xz(sketch, 207.8, -3.8, z1, 2.3, z2)
    world_rect_xz(sketch, 207.8, 297.7, z1, 303.8, z2)
one_side('04_后盖板左右互锁小榫_厚2.2深6mm', sketch, 'y', True, 2.2,
         adsk.fusion.FeatureOperations.JoinFeatureOperation)
if root.bRepBodies.count != 4:
    raise RuntimeError('后盖板小榫未与后板合并')

# 小榫外侧15°浅倒扣，凸高0.6，向榫内底部搭接0.1。
barb_run = 0.6/math.tan(math.radians(15))
for index, (z1, z2) in enumerate(rear_z, 1):
    plane = offset_plane(root.xYConstructionPlane, 'z', z1, f'04_互锁倒扣平面_{index}')
    sketch = root.sketches.add(plane)
    sketch.name = f'04_左右互锁榫15度倒扣草图_{index}'
    for shoulder, low in [(-0.4, -0.4-barb_run), (300.4, 300.4+barb_run)]:
        world_polygon_xy(sketch, z1, [
            (low, 209.9), (low, 210.0), (shoulder, 210.6), (shoulder, 209.9)
        ])
    one_side(f'04_左右互锁榫15度浅倒扣_{index}', sketch, 'z', True, 12,
             adsk.fusion.FeatureOperations.JoinFeatureOperation)

# 六个小榫共12条根部边R1。
root_edges = adsk.core.ObjectCollection.create()
for edge in rear.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    dz = (box.maxPoint.z-box.minPoint.z)*10
    cx = (box.minPoint.x+box.maxPoint.x)*5
    cz = (box.minPoint.z+box.maxPoint.z)*5
    if (dx < 0.01 and abs(dy-2.2) < 0.01 and dz < 0.01
            and abs(box.minPoint.y*10-207.8) < 0.01
            and any(abs(cx-x) < 0.01 for x in (2.2, 297.8))
            and any(abs(cz-z) < 0.01 for pair in rear_z for z in pair)):
        root_edges.add(edge)
if root_edges.count != 12:
    raise RuntimeError(f'互锁小榫根部边数量异常: {root_edges.count}，预期12')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    root_edges, adsk.core.ValueInput.createByString('TenonRootR'), False)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '04_互锁小榫根部_R1_12边'

# 底座后榫3个底部开口母槽，单边间隙0.2。
rear_x = [(54, 66), (144, 156), (234, 246)]
sketch = root.sketches.add(main_plane)
sketch.name = '04_后盖板底座母槽草图_单边0.2mm'
for x1, x2 in rear_x:
    world_rect_xz(sketch, 207.8, x1-0.2, -0.2, x2+0.2, 2.4)
through_cut('04_后盖板底座母槽_3个_单边0.2mm', sketch, rear)

# R1根部局部让位，从前表面向后1.2。
sketch = root.sketches.add(main_plane)
sketch.name = '04_后盖板底座榫根让位草图'
for x1, x2 in rear_x:
    world_rect_xz(sketch, 207.8, x1-1.2, -0.2, x2+1.2, 2.4)
one_side('04_后盖板底座榫根让位_深1.2mm', sketch, 'y', True, 1.2,
         adsk.fusion.FeatureOperations.CutFeatureOperation, rear)

# 47条竖向格栅；下沿4.6，确保底部母槽顶与格栅间实料2.2。
sketch = root.sketches.add(main_plane)
sketch.name = '04_后盖板竖向格栅草图_47缝'
for index in range(47):
    x1 = 5.4 + index*6.2
    world_rect_xz(sketch, 207.8, x1, 4.6, x1+4, 197.8)
if sketch.profiles.count != 47:
    raise RuntimeError(f'后格栅轮廓数量异常: {sketch.profiles.count}')
through_cut('04_后盖板竖向格栅_47缝4mm_筋2.2mm', sketch, rear)

# 后上沿10贯通出线槽，槽底Z=200。
sketch = root.sketches.add(main_plane)
sketch.name = '04_后上沿出线槽草图_深10mm'
world_rect_xz(sketch, 207.8, 2.2, 200, 297.8, 210.2)
through_cut('04_后上沿贯通出线槽_深10mm', sketch, rear)

# 出线槽形成的新上沿与底部外轮廓四角R3。
outer_edges = adsk.core.ObjectCollection.create()
for edge in rear.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    dz = (box.maxPoint.z-box.minPoint.z)*10
    cx = (box.minPoint.x+box.maxPoint.x)*5
    cz = (box.minPoint.z+box.maxPoint.z)*5
    if (dx < 0.01 and abs(dy-2.2) < 0.01 and dz < 0.01
            and any(abs(cx-x) < 0.01 for x in (2.2, 297.8))
            and any(abs(cz-z) < 0.01 for z in (0, 200))):
        outer_edges.add(edge)
if outer_edges.count != 4:
    raise RuntimeError(f'后盖板外轮廓边数量异常: {outer_edges.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    outer_edges, adsk.core.ValueInput.createByString('OuterR'), False)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '04_后盖板外轮廓_R3'

for body in existing.values():
    body.isVisible = True
for name, body in existing.items():
    if abs(body.physicalProperties.volume-volumes_before[name]) > 0.000001:
        raise RuntimeError('后盖板建模误改了既有实体: ' + name)
if root.bRepBodies.count != 4:
    raise RuntimeError('步骤4完成后实体数量不是4')
non_manifold = {body.name: sum(1 for edge in body.edges if edge.faces.count > 2)
                for body in root.bRepBodies}
if any(non_manifold.values()):
    raise RuntimeError(f'存在非流形边: {non_manifold}')
box = rear.boundingBox
print({'step': 4, 'bodies': [body.name for body in root.bRepBodies],
       'existing_volumes_unchanged': True, 'non_manifold': non_manifold,
       'rear_base_mortise_count': 3, 'rear_interlock_tenon_count': 6,
       'interlock_tenon_root_R1_edges': root_edges.count,
       'barb_angle_deg': 15.0, 'barb_projection_mm': 0.6,
       'rear_grille_slot_count': 47, 'slot_mm': 4.0, 'rib_mm': 2.2,
       'grille_bottom_z_mm': 4.6, 'bottom_ligament_mm': 2.2,
       'cable_slot_depth_mm': 10.0, 'cable_slot_bottom_z_mm': 200.0,
       'rear_outer_R3_edges': outer_edges.count,
       'rear_bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                        'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
