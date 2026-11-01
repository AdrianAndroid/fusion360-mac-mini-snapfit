design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤7要求当前为单一实体')
if root.features.extrudeFeatures.itemByName('07_右侧拎带孔_直径9mm'):
    raise RuntimeError('左右拎带孔已存在，停止以避免重复建模')
for name, expression in {
    'HandleHoleD': '9 mm', 'HandleRadialW': '4.5 mm', 'HandleBossT': '4.5 mm',
    'HandleCenterY': '105 mm', 'HandleCenterZ': '105 mm',
    'HandleJoinOverlap': '0.1 mm',
}.items():
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expression), 'mm', name)


def world_to_sketch(sketch, point):
    inverse = sketch.transform.copy()
    if not inverse.invert():
        raise RuntimeError('草图坐标逆变换失败: ' + sketch.name)
    point.transformBy(inverse)
    return point


def sketch_normal_x(sketch):
    return sketch.transform.getCell(0, 2)


def add_circle(sketch, radius_mm):
    center = world_to_sketch(sketch, adsk.core.Point3D.create(
        sketch.transform.getCell(0, 3), 10.5, 10.5))
    # 圆心必须使用草图局部Z=0；平面X坐标由变换矩阵给出。
    center.z = 0
    return sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius_mm/10)


def select_single_circle_profile(sketch, diameter_mm):
    matches = []
    for profile in sketch.profiles:
        box = profile.boundingBox
        dx = (box.maxPoint.x-box.minPoint.x)*10
        dy = (box.maxPoint.y-box.minPoint.y)*10
        if abs(dx-diameter_mm) < 0.01 and abs(dy-diameter_mm) < 0.01:
            matches.append(profile)
    if len(matches) != 1:
        raise RuntimeError(f'{sketch.name} 圆形轮廓数量异常: {len(matches)}')
    return matches[0]


def add_one_sided_join(sketch, profile, inward_positive, distance_expression, name):
    feature_input = root.features.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
    normal_x = sketch_normal_x(sketch)
    is_positive = normal_x > 0 if inward_positive else normal_x < 0
    direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if is_positive
                 else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    feature_input.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByString(distance_expression)),
        direction, adsk.core.ValueInput.createByString('0 deg'))
    feature = root.features.extrudeFeatures.add(feature_input)
    feature.name = name
    if root.bRepBodies.count != 1:
        raise RuntimeError(name + ' 未与壳体连接为单一实体')
    return feature


def add_external_boss(sketch, name):
    profile = select_single_circle_profile(sketch, 18.0)
    feature_input = root.features.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
    outward_positive = sketch_normal_x(sketch) < 0 if sketch.name.startswith('07_草图_左') else sketch_normal_x(sketch) > 0
    inward_distance = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('HandleJoinOverlap'))
    outward_distance = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('HandleBossT'))
    first = outward_distance if outward_positive else inward_distance
    second = inward_distance if outward_positive else outward_distance
    feature_input.setTwoSidesExtent(
        first, second, adsk.core.ValueInput.createByString('0 deg'),
        adsk.core.ValueInput.createByString('0 deg'))
    feature = root.features.extrudeFeatures.add(feature_input)
    feature.name = name
    if root.bRepBodies.count != 1:
        raise RuntimeError(name + ' 未与壳体连接为单一实体')
    return feature


def add_hole(sketch, name):
    profile = select_single_circle_profile(sketch, 9.0)
    feature_input = root.features.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
    outward_positive = sketch_normal_x(sketch) < 0 if sketch.name.startswith('07_草图_左') else sketch_normal_x(sketch) > 0
    inward = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT'))
    outward = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('HandleBossT'))
    first = outward if outward_positive else inward
    second = inward if outward_positive else outward
    feature_input.setTwoSidesExtent(
        first, second, adsk.core.ValueInput.createByString('0 deg'),
        adsk.core.ValueInput.createByString('0 deg'))
    feature = root.features.extrudeFeatures.add(feature_input)
    feature.name = name
    return feature


# 左窗中央连接筋：宽2.2，向上下边框各搭接0.1，保持散热窗周边8mm边框。
left_web_sketch = root.sketches.add(root.yZConstructionPlane)
left_web_sketch.name = '07_草图_左孔连接筋_厚2.2mm'
point_one = world_to_sketch(left_web_sketch, adsk.core.Point3D.create(0, 10.39, 0.79))
point_two = world_to_sketch(left_web_sketch, adsk.core.Point3D.create(0, 10.61, 20.21))
left_web_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point_one, point_two)
if left_web_sketch.profiles.count != 1:
    raise RuntimeError('左孔连接筋轮廓数量异常')
web = add_one_sided_join(
    left_web_sketch, left_web_sketch.profiles.item(0), True, 'WallT',
    '07_左孔连接筋_厚2.2mm')

# 连接筋与上下边框的四条根部边R2。
web_roots = adsk.core.ObjectCollection.create()
for edge in body.edges:
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
            and any(abs(cz-z) < 0.01 for z in (8.0, 202.0))):
        web_roots.add(edge)
if web_roots.count != 4:
    raise RuntimeError(f'左孔连接筋根边数量异常: {web_roots.count}，预期4')
web_fillet_input = root.features.filletFeatures.createInput()
web_fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    web_roots, adsk.core.ValueInput.createByString('DividerRootR'), False)
web_fillet = root.features.filletFeatures.add(web_fillet_input)
web_fillet.name = '07_左孔连接筋根部_R2'

# 左中心加强垫填回散热窗中心，与2.2连接筋重叠成一体。
left_pad_sketch = root.sketches.add(root.yZConstructionPlane)
left_pad_sketch.name = '07_草图_左孔中心加强垫_直径18mm'
add_circle(left_pad_sketch, 9.0)
left_pad = add_one_sided_join(
    left_pad_sketch, select_single_circle_profile(left_pad_sketch, 18.0), True, 'WallT',
    '07_左孔中心加强垫_直径18mm')

# 左凸台向外4.5、向内搭接0.1。
left_boss_sketch = root.sketches.add(root.yZConstructionPlane)
left_boss_sketch.name = '07_草图_左侧拎带加强台_外径18mm'
add_circle(left_boss_sketch, 9.0)
left_boss = add_external_boss(left_boss_sketch, '07_左侧拎带加强台_径向4.5_加厚4.5mm')

# 右侧X=300草图平面。
right_plane_input = root.constructionPlanes.createInput()
right_plane_input.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByString('OuterL'))
right_plane = root.constructionPlanes.add(right_plane_input)
right_plane.name = '07_右侧外壁草图平面_X300mm'
if abs(right_plane.geometry.origin.x-30.0) > 0.001:
    raise RuntimeError(f'右侧草图平面位置异常: X={right_plane.geometry.origin.x*10}mm')
right_boss_sketch = root.sketches.add(right_plane)
right_boss_sketch.name = '07_草图_右侧拎带加强台_外径18mm'
add_circle(right_boss_sketch, 9.0)
right_boss = add_external_boss(right_boss_sketch, '07_右侧拎带加强台_径向4.5_加厚4.5mm')

# 两孔只穿凸台和对应侧壁，不切到内部隔板。
left_hole_sketch = root.sketches.add(root.yZConstructionPlane)
left_hole_sketch.name = '07_草图_左侧拎带孔_直径9mm'
add_circle(left_hole_sketch, 4.5)
left_hole = add_hole(left_hole_sketch, '07_左侧拎带孔_直径9mm')
right_hole_sketch = root.sketches.add(right_plane)
right_hole_sketch.name = '07_草图_右侧拎带孔_直径9mm'
add_circle(right_hole_sketch, 4.5)
right_hole = add_hole(right_hole_sketch, '07_右侧拎带孔_直径9mm')

hole_cylinders = []
boss_cylinders = []
for face in body.faces:
    cylinder = adsk.core.Cylinder.cast(face.geometry)
    if not cylinder:
        continue
    axis = cylinder.axis
    if abs(axis.x) > 0.999 and abs(cylinder.radius-0.45) < 0.001:
        hole_cylinders.append(face)
    if abs(axis.x) > 0.999 and abs(cylinder.radius-0.9) < 0.001:
        boss_cylinders.append(face)
non_manifold_count = sum(1 for edge in body.edges if edge.faces.count > 2)
box = body.boundingBox
if len(hole_cylinders) != 2 or len(boss_cylinders) != 2:
    raise RuntimeError(f'拎带孔或凸台圆柱面数量异常: 孔{len(hole_cylinders)}，台{len(boss_cylinders)}')
if root.bRepBodies.count != 1 or non_manifold_count:
    raise RuntimeError('步骤7完成后存在多实体或非流形边')
if abs(box.minPoint.x*10+4.5) > 0.01 or abs(box.maxPoint.x*10-304.5) > 0.01:
    raise RuntimeError('左右加强台外部加厚尺寸异常')
print({'step': 7, 'hole_diameter_mm': 9.0, 'hole_centers_yz_mm': [105.0, 105.0],
       'boss_outer_diameter_mm': 18.0, 'radial_reinforcement_mm': 4.5,
       'external_boss_thickness_mm': 4.5, 'join_overlap_mm': 0.1,
       'left_web_thickness_mm': 2.2, 'left_web_root_fillet_edges': web_roots.count,
       'hole_cylinder_count': len(hole_cylinders), 'boss_cylinder_count': len(boss_cylinders),
       'body_count': 1, 'non_manifold_edge_count': non_manifold_count,
       'x_range_with_bosses_mm': [box.minPoint.x*10, box.maxPoint.x*10],
       'features': [web.name, web_fillet.name, left_pad.name, left_boss.name,
                    right_boss.name, left_hole.name, right_hole.name]})
