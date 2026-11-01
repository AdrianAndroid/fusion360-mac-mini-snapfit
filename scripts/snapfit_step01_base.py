import math

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
if root.bRepBodies.count != 0:
    raise RuntimeError('步骤1要求空文档')
if design.unitsManager.defaultLengthUnits != 'mm':
    raise RuntimeError('文档单位不是mm')


def set_parameter(name, expression, comment=''):
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        unit = 'deg' if name == 'BarbAngle' else 'mm'
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expression), unit, comment or name)


for name, expression in {
    'OuterL': '300 mm', 'OuterD': '210 mm', 'OuterH': '210 mm',
    'WallT': '2.2 mm', 'OuterR': '3 mm', 'DividerRootR': '2 mm',
    'TenonT': '2.2 mm', 'TenonDepth': '6 mm', 'TenonRootR': '1 mm',
    'SnapClearance': '0.2 mm', 'BarbAngle': '15 deg', 'BarbH': '0.6 mm',
    'JoinOverlap': '0.1 mm', 'FootH': '5 mm', 'FootWallT': '2.2 mm',
    'BottomSlotW': '4 mm', 'BottomRibW': '2.2 mm', 'PartitionTopZ': '200.65 mm',
    'MacSlotW': '36.55 mm', 'MacSlotD': '198.45 mm', 'MacSlotH': '198.45 mm',
    'HDD35SlotW': '26.85 mm', 'HDD35SlotD': '102.35 mm', 'HDD35SlotH': '146.75 mm',
    'HDD25SlotW': '10.25 mm', 'HDD25SlotD': '70.6 mm',
    'HDD25SlotH': '100.75 mm', 'HubSlotW': '32.75 mm', 'HubSlotD': '105.75 mm',
    'HubSlotH': '120.75 mm', 'CableChannelW': '182.6 mm',
}.items():
    set_parameter(name, expression)


def rect(sketch, x1, y1, x2, y2):
    return sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(x1/10, y1/10, 0),
        adsk.core.Point3D.create(x2/10, y2/10, 0))


def profiles_of(sketch):
    profiles = adsk.core.ObjectCollection.create()
    for profile in sketch.profiles:
        profiles.add(profile)
    return profiles


def extrude_xy(name, rectangles, height_expression, operation):
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name + '_草图'
    for coordinates in rectangles:
        rect(sketch, *coordinates)
    profiles = profiles_of(sketch)
    feature_input = root.features.extrudeFeatures.createInput(profiles, operation)
    feature_input.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(height_expression)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
        adsk.core.ValueInput.createByString('0 deg'))
    feature = root.features.extrudeFeatures.add(feature_input)
    feature.name = name
    return feature


base = extrude_xy(
    '01_底板_壁厚2.2mm', [(2.2, 0, 297.8, 207.8)], 'WallT',
    adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
body = root.bRepBodies.item(0)
body.name = '01_底座总成'

# 三边各3个公榫；根部向底板内搭接0.1，向外有效插入深度严格为6。
side_y = [(24, 36), (99, 111), (174, 186)]
rear_x = [(54, 66), (144, 156), (234, 246)]
tenons = []
for y1, y2 in side_y:
    tenons.append((-3.8, y1, 2.3, y2))
    tenons.append((297.7, y1, 303.8, y2))
for x1, x2 in rear_x:
    tenons.append((x1, 207.7, x2, 213.8))
extrude_xy('01_底座三边公榫_9个_厚2.2深6mm', tenons, 'TenonT',
           adsk.fusion.FeatureOperations.JoinFeatureOperation)
if root.bRepBodies.count != 1:
    raise RuntimeError('底座公榫未合并为单一实体')


def offset_plane(reference, axis, target_mm, name):
    normal = getattr(reference.geometry.normal, axis)
    offset = target_mm / normal
    plane_input = root.constructionPlanes.createInput()
    plane_input.setByOffset(reference, adsk.core.ValueInput.createByString(f'{offset} mm'))
    plane = root.constructionPlanes.add(plane_input)
    plane.name = name
    actual = getattr(plane.geometry.origin, axis) * 10
    if abs(actual-target_mm) > 0.001:
        raise RuntimeError(f'{name} 位置异常: {actual}')
    return plane


def world_to_sketch(sketch, point):
    inverse = sketch.transform.copy()
    if not inverse.invert():
        raise RuntimeError('草图逆变换失败: ' + sketch.name)
    point.transformBy(inverse)
    return point


def add_world_polygon(sketch, points):
    local = [world_to_sketch(sketch, p) for p in points]
    for index in range(len(local)):
        sketch.sketchCurves.sketchLines.addByTwoPoints(local[index], local[(index+1) % len(local)])


def extrude_along_normal(sketch, axis, positive, width_mm, name):
    _, _, _, normal_vector = sketch.transform.getAsCoordinateSystem()
    normal = getattr(normal_vector, axis)
    is_positive = normal > 0 if positive else normal < 0
    direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if is_positive
                 else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    feature_input = root.features.extrudeFeatures.createInput(
        profiles_of(sketch), adsk.fusion.FeatureOperations.JoinFeatureOperation)
    feature_input.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{width_mm} mm')),
        direction, adsk.core.ValueInput.createByString('0 deg'))
    feature = root.features.extrudeFeatures.add(feature_input)
    feature.name = name
    if root.bRepBodies.count != 1:
        raise RuntimeError(name + ' 未合并为单一实体')
    return feature


barb_run = 0.6 / math.tan(math.radians(15))
# 倒扣斜坡严格15°；底部向榫头内搭接0.1，外侧有效凸高0.6。
for index, (y1, y2) in enumerate(side_y, 1):
    plane = offset_plane(root.xZConstructionPlane, 'y', y1, f'01_侧榫倒扣平面_{index}')
    sketch = root.sketches.add(plane)
    sketch.name = f'01_左右榫15度倒扣草图_{index}'
    for shoulder, low in [(-0.4, -0.4-barb_run), (300.4, 300.4+barb_run)]:
        add_world_polygon(sketch, [
            adsk.core.Point3D.create(low/10, y1/10, 0.21),
            adsk.core.Point3D.create(low/10, y1/10, 0.22),
            adsk.core.Point3D.create(shoulder/10, y1/10, 0.28),
            adsk.core.Point3D.create(shoulder/10, y1/10, 0.21),
        ])
    extrude_along_normal(sketch, 'y', True, 12, f'01_左右榫15度浅倒扣_{index}')
for index, (x1, x2) in enumerate(rear_x, 1):
    plane = offset_plane(root.yZConstructionPlane, 'x', x1, f'01_后榫倒扣平面_{index}')
    sketch = root.sketches.add(plane)
    sketch.name = f'01_后榫15度倒扣草图_{index}'
    add_world_polygon(sketch, [
        adsk.core.Point3D.create(x1/10, (210.4+barb_run)/10, 0.21),
        adsk.core.Point3D.create(x1/10, (210.4+barb_run)/10, 0.22),
        adsk.core.Point3D.create(x1/10, 21.04, 0.28),
        adsk.core.Point3D.create(x1/10, 21.04, 0.21),
    ])
    extrude_along_normal(sketch, 'x', True, 12, f'01_后榫15度浅倒扣_{index}')

# 每个公榫两条竖向根部边，共18条，R1。
root_edges = adsk.core.ObjectCollection.create()
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    dz = (box.maxPoint.z-box.minPoint.z)*10
    cx = (box.minPoint.x+box.maxPoint.x)*5
    cy = (box.minPoint.y+box.maxPoint.y)*5
    if not (dx < 0.01 and dy < 0.01 and abs(dz-2.2) < 0.01 and abs(box.minPoint.z) < 0.001):
        continue
    side_root = (any(abs(cx-x) < 0.01 for x in (2.2, 297.8))
                 and any(abs(cy-y) < 0.01 for pair in side_y for y in pair))
    rear_root = (abs(cy-207.8) < 0.01
                 and any(abs(cx-x) < 0.01 for pair in rear_x for x in pair))
    if side_root or rear_root:
        root_edges.add(edge)
if root_edges.count != 18:
    raise RuntimeError(f'公榫根部边数量异常: {root_edges.count}，预期18')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    root_edges, adsk.core.ValueInput.createByString('TenonRootR'), False)
root_fillet = root.features.filletFeatures.add(fillet_input)
root_fillet.name = '01_底座公榫根部_R1_18边'

# 前壁与底座一体；左右侧板和后盖板为后续独立零件。
extrude_xy('01_前壁_高210mm_厚2.2mm', [(2.2, 0, 297.8, 2.2)], 'OuterH',
           adsk.fusion.FeatureOperations.JoinFeatureOperation)

# 三块主隔板顶部Z=200.65，距壳顶9.35形成走线空间。
extrude_xy('01_三块主隔板_厚2.2mm', [
    (38.75, 2.2, 40.95, 202.85),
    (67.8, 2.2, 70.0, 202.85),
    (80.25, 2.2, 82.45, 202.85),
], 'PartitionTopZ', adsk.fusion.FeatureOperations.JoinFeatureOperation)
extrude_xy('01_Mac后限位筋_厚2.2mm', [(2.2, 200.65, 38.75, 202.85)],
           'MacSlotH + WallT', adsk.fusion.FeatureOperations.JoinFeatureOperation)
extrude_xy('01_3.5寸后限位筋_厚2.2mm', [(40.95, 104.55, 67.8, 106.75)],
           'HDD35SlotH + WallT', adsk.fusion.FeatureOperations.JoinFeatureOperation)
extrude_xy('01_2.5寸后限位筋_厚2.2mm', [(70.0, 72.8, 80.25, 75.0)],
           'HDD25SlotH + WallT', adsk.fusion.FeatureOperations.JoinFeatureOperation)
extrude_xy('01_Hub后限位筋_厚2.2mm', [(82.45, 107.95, 115.2, 110.15)],
           'HubSlotH + WallT', adsk.fusion.FeatureOperations.JoinFeatureOperation)

# 隔板及限位筋根边R2。
partition_x = [38.75, 40.95, 67.8, 70.0, 80.25, 82.45]
stop_y = [200.65, 202.85, 104.55, 106.75, 72.8, 75.0, 107.95, 110.15]
divider_roots = adsk.core.ObjectCollection.create()
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    if abs(box.minPoint.z-0.22) > 0.001 or abs(box.maxPoint.z-0.22) > 0.001:
        continue
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    cx = (box.minPoint.x+box.maxPoint.x)*5
    cy = (box.minPoint.y+box.maxPoint.y)*5
    is_partition = dx < 0.01 and dy > 3 and any(abs(cx-x) < 0.01 for x in partition_x)
    is_stop = dy < 0.01 and dx > 10 and any(abs(cy-y) < 0.01 for y in stop_y)
    if is_partition or is_stop:
        divider_roots.add(edge)
if divider_roots.count != 19:
    raise RuntimeError(f'隔板根边数量异常: {divider_roots.count}，预期19')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    divider_roots, adsk.core.ValueInput.createByString('DividerRootR'), False)
divider_fillet = root.features.filletFeatures.add(fillet_input)
divider_fillet.name = '01_隔板与限位筋根部_R2_19边'

# 支撑脚仅位于底座 footprint，避免与独立侧板/后板相交。
foot_plane_input = root.constructionPlanes.createInput()
foot_plane_input.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByString('JoinOverlap'))
foot_plane = root.constructionPlanes.add(foot_plane_input)
foot_plane.name = '01_支撑脚搭接平面_Z0.1mm'
foot_sketch = root.sketches.add(foot_plane)
foot_sketch.name = '01_支撑脚环形草图_壁厚2.2mm'
rect(foot_sketch, 2.2, 0, 297.8, 207.8)
rect(foot_sketch, 4.4, 2.2, 295.6, 205.6)
ring_profiles = [p for p in foot_sketch.profiles if p.profileLoops.count == 2]
if len(ring_profiles) != 1:
    raise RuntimeError('支撑脚环形轮廓异常')
foot_input = root.features.extrudeFeatures.createInput(
    ring_profiles[0], adsk.fusion.FeatureOperations.JoinFeatureOperation)
foot_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('FootH + JoinOverlap')),
    adsk.fusion.ExtentDirections.NegativeExtentDirection,
    adsk.core.ValueInput.createByString('0 deg'))
foot = root.features.extrudeFeatures.add(foot_input)
foot.name = '01_支撑脚_高5mm_壁厚2.2mm'
foot_edges = adsk.core.ObjectCollection.create()
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    dz = (box.maxPoint.z-box.minPoint.z)*10
    cx = (box.minPoint.x+box.maxPoint.x)*5
    cy = (box.minPoint.y+box.maxPoint.y)*5
    if (dx < 0.01 and dy < 0.01
            and abs(box.minPoint.z*10+5) < 0.01
            and any(abs(cx-x) < 0.01 for x in (2.2, 297.8))
            and any(abs(cy-y) < 0.01 for y in (0, 207.8))):
        foot_edges.add(edge)
if foot_edges.count != 4:
    raise RuntimeError(f'支撑脚外竖角数量异常: {foot_edges.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    foot_edges, adsk.core.ValueInput.createByString('OuterR'), False)
foot_fillet = root.features.filletFeatures.add(fillet_input)
foot_fillet.name = '01_支撑脚外竖角_R3'

# 底部32条横向格栅，缝4、筋2.2。
grille_sketch = root.sketches.add(root.xYConstructionPlane)
grille_sketch.name = '01_底部横向格栅草图_32缝'
pitch = 6.2
occupied = 32*4 + 31*2.2
y_start = 4.4 + ((205.6-4.4)-occupied)/2
for index in range(32):
    y1 = y_start + index*pitch
    rect(grille_sketch, 4.4, y1, 295.6, y1+4)
grille_input = root.features.extrudeFeatures.createInput(
    profiles_of(grille_sketch), adsk.fusion.FeatureOperations.CutFeatureOperation)
grille_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg'))
grille = root.features.extrudeFeatures.add(grille_input)
grille.name = '01_底部横向格栅_32缝4mm_筋2.2mm'

non_manifold = sum(1 for edge in body.edges if edge.faces.count > 2)
if root.bRepBodies.count != 1 or non_manifold:
    raise RuntimeError('步骤1完成后存在多实体或非流形边')
# 仓位坐标自检。
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
       'tenon_insert_depth_mm': 6.0, 'tenon_root_R1_edges': root_edges.count,
       'barb_angle_deg': 15.0, 'barb_projection_mm': 0.6,
       'barb_ramp_length_mm': barb_run,
       'divider_root_R2_edges': divider_roots.count,
       'partition_top_z_mm': 200.65, 'top_wiring_gap_mm': 9.35,
       'bottom_slot_count': 32, 'bottom_slot_mm': 4.0, 'bottom_rib_mm': 2.2,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
