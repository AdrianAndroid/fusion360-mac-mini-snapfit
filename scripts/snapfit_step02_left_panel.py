import math

design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤2要求当前仅有底座总成')
base = root.bRepBodies.item(0)
if base.name != '01_底座总成':
    raise RuntimeError('未找到底座总成')
base_volume_before = base.physicalProperties.volume
# 当前桥接的多实体切除会作用于可见实体；临时隐藏底座，确保只切左板。
base.isVisible = False


def add_parameter(name, expression):
    if not design.userParameters.itemByName(name):
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expression), 'mm', name)


for name, expression in {
    'VentBorder': '8 mm', 'HandleHoleD': '9 mm', 'HandleBossD': '18 mm',
    'HandleBossH': '4.5 mm', 'CenterRibT': '2.2 mm', 'TenonW': '12 mm',
    'RootReliefDepth': '1.2 mm',
}.items():
    add_parameter(name, expression)


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
    return sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius/10)


def profiles_of(sketch):
    profiles = adsk.core.ObjectCollection.create()
    for profile in sketch.profiles:
        profiles.add(profile)
    return profiles


def sketch_normal_x(sketch):
    _, _, _, normal = sketch.transform.getAsCoordinateSystem()
    return normal.x


def one_side(name, sketch, distance, positive_x, operation, target=None):
    feature_input = root.features.extrudeFeatures.createInput(profiles_of(sketch), operation)
    if target is not None:
        targets = adsk.core.ObjectCollection.create()
        targets.add(target)
        feature_input.targetBodies = targets
    normal = sketch_normal_x(sketch)
    is_positive = normal > 0 if positive_x else normal < 0
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


# 左侧板X=0–2.2，作为独立新实体。
sketch = root.sketches.add(root.yZConstructionPlane)
sketch.name = '02_左侧板外轮廓草图_210x210mm'
world_rect(sketch, 0, 0, 0, 210, 210)
one_side('02_左侧板基体_厚2.2mm', sketch, 2.2, True,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
if root.bRepBodies.count != 2:
    raise RuntimeError('左侧板未形成独立实体')
left = next(body for body in root.bRepBodies if body.entityToken != base.entityToken)
left.name = '02_左侧板'

# 平板外轮廓四个尖角R3，圆角在YZ面内，不受2.2板厚限制。
outer_edges = adsk.core.ObjectCollection.create()
for edge in left.edges:
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
    raise RuntimeError(f'左侧板外轮廓边数量异常: {outer_edges.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    outer_edges, adsk.core.ValueInput.createByString('OuterR'), False)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '02_左侧板外轮廓_R3'

# Mac mini散热窗，四周保留8实体边框。
sketch = root.sketches.add(root.yZConstructionPlane)
sketch.name = '02_Mac散热窗草图_边框8mm'
world_rect(sketch, 0, 8, 8, 202, 202)
through_cut('02_Mac大面积散热窗_边框8mm', sketch, left)

# 底座左榫3个底部开口母槽，以及后盖板小榫3个后端开口母槽。
side_y = [(24, 36), (99, 111), (174, 186)]
rear_z = [(24, 36), (99, 111), (174, 186)]
sketch = root.sketches.add(root.yZConstructionPlane)
sketch.name = '02_左侧板六个贯通母槽草图_单边间隙0.2mm'
for y1, y2 in side_y:
    world_rect(sketch, 0, y1-0.2, -0.2, y2+0.2, 2.4)
for z1, z2 in rear_z:
    world_rect(sketch, 0, 207.6, z1-0.2, 210.2, z2+0.2)
through_cut('02_左侧板母槽_底3后3_单边0.2mm', sketch, left)

# R1榫根在内侧1.2范围需等形让位；主槽仍保持0.2单边间隙。
relief_plane_input = root.constructionPlanes.createInput()
relief_plane_input.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByString('RootReliefDepth - SnapClearance'))
relief_plane = root.constructionPlanes.add(relief_plane_input)
relief_plane.name = '02_左侧板榫根让位平面_X1mm'
sketch = root.sketches.add(relief_plane)
sketch.name = '02_左侧板R1榫根让位草图'
for y1, y2 in side_y:
    world_rect(sketch, 1.0, y1-1.2, -0.2, y2+1.2, 2.4)
for z1, z2 in rear_z:
    world_rect(sketch, 1.0, 207.6, z1-1.2, 210.2, z2+1.2)
one_side('02_左侧板R1榫根让位_深1.2mm', sketch, 1.2, True,
         adsk.fusion.FeatureOperations.CutFeatureOperation, left)

# 中央2.2连接筋跨上下窗框，两端各搭接0.1。
sketch = root.sketches.add(root.yZConstructionPlane)
sketch.name = '02_左窗中央连接筋草图_厚2.2mm'
world_rect(sketch, 0, 103.9, 7.9, 106.1, 202.1)
one_side('02_左窗中央连接筋_厚2.2mm', sketch, 2.2, True,
         adsk.fusion.FeatureOperations.JoinFeatureOperation)

# 中心R9加强垫与连接筋一体。
sketch = root.sketches.add(root.yZConstructionPlane)
sketch.name = '02_左侧中心加强垫草图_R9'
world_circle(sketch, 0, 105, 105, 9)
one_side('02_左侧中心加强垫_R9', sketch, 2.2, True,
         adsk.fusion.FeatureOperations.JoinFeatureOperation)

# 外凸4.5的加强台，向板内/板面搭接0.1。
boss_plane_input = root.constructionPlanes.createInput()
boss_plane_input.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByString('JoinOverlap'))
boss_plane = root.constructionPlanes.add(boss_plane_input)
boss_plane.name = '02_左侧拎带凸台搭接平面_X0.1mm'
sketch = root.sketches.add(boss_plane)
sketch.name = '02_左侧拎带凸台草图_R9'
world_circle(sketch, 0.1, 105, 105, 9)
one_side('02_左侧拎带凸台_外厚4.5mm', sketch, 4.6, False,
         adsk.fusion.FeatureOperations.JoinFeatureOperation)

# Ø9拎带孔只切左侧板，避免任何其他实体被误切。
sketch = root.sketches.add(root.yZConstructionPlane)
sketch.name = '02_左侧拎带孔草图_D9'
world_circle(sketch, 0, 105, 105, 4.5)
through_cut('02_左侧拎带孔_D9', sketch, left, 6.0)

# 连接筋四条根边R2。
rib_roots = adsk.core.ObjectCollection.create()
for edge in left.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    dx = (box.maxPoint.x-box.minPoint.x)*10
    dy = (box.maxPoint.y-box.minPoint.y)*10
    dz = (box.maxPoint.z-box.minPoint.z)*10
    cy = (box.minPoint.y+box.maxPoint.y)*5
    cz = (box.minPoint.z+box.maxPoint.z)*5
    if (abs(dx-2.2) < 0.01 and dy < 0.01 and dz < 0.01
            and any(abs(cy-y) < 0.01 for y in (103.9, 106.1))
            and any(abs(cz-z) < 0.01 for z in (8, 202))):
        rib_roots.add(edge)
if rib_roots.count != 4:
    raise RuntimeError(f'左窗连接筋根边数量异常: {rib_roots.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    rib_roots, adsk.core.ValueInput.createByString('DividerRootR'), False)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '02_左窗连接筋根部_R2_4边'

base.isVisible = True
if abs(base.physicalProperties.volume-base_volume_before) > 0.000001:
    raise RuntimeError('左侧板建模误改了底座体积')
if root.bRepBodies.count != 2:
    raise RuntimeError('步骤2完成后实体数量不是2')
non_manifold = {body.name: sum(1 for edge in body.edges if edge.faces.count > 2)
                for body in root.bRepBodies}
if any(non_manifold.values()):
    raise RuntimeError(f'存在非流形边: {non_manifold}')
box = left.boundingBox
print({'step': 2, 'bodies': [body.name for body in root.bRepBodies],
       'base_volume_unchanged': True, 'non_manifold': non_manifold,
       'left_outer_R3_edges': outer_edges.count,
       'vent_border_mm': 8.0, 'vent_opening_mm': [194.0, 194.0],
       'base_mortise_count': 3, 'rear_interlock_mortise_count': 3,
       'mortise_width_mm': 12.4, 'single_side_clearance_mm': 0.2,
       'root_relief_depth_mm': 1.2, 'rib_root_R2_edges': rib_roots.count,
       'handle_hole_diameter_mm': 9.0, 'boss_outer_diameter_mm': 18.0,
       'boss_outward_thickness_mm': 4.5,
       'left_bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                        'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
