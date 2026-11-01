design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤5要求当前只有1个实体')

parameter = design.userParameters.itemByName('HandleBossRadial')
if parameter:
    parameter.expression = '4.5 mm'
else:
    design.userParameters.add(
        'HandleBossRadial', adsk.core.ValueInput.createByString('4.5 mm'),
        'mm', '拎带孔加强台径向加宽'
    )


def profile_xy_size(profile):
    box = profile.boundingBox
    return (box.maxPoint.x - box.minPoint.x,
            box.maxPoint.y - box.minPoint.y)


def side_face(body, x_cm, normal_sign):
    matches = []
    for face in body.faces:
        plane = adsk.core.Plane.cast(face.geometry)
        if not plane:
            continue
        if (plane.normal.x * normal_sign > 0.999 and
                abs(face.boundingBox.minPoint.x - x_cm) < 0.001 and
                abs(face.boundingBox.maxPoint.x - x_cm) < 0.001):
            matches.append(face)
    if len(matches) != 1:
        raise RuntimeError(f'侧壁面数量异常: X={x_cm}, count={len(matches)}')
    return matches[0]


results = []
for side, x_cm, normal_sign in [('左', 0.0, -1), ('右', 39.0, 1)]:
    body = root.bRepBodies.itemByName('01_外框壳体')
    existing_sketch = root.sketches.itemByName(f'05_{side}拎带孔及加强台草图')
    if existing_sketch:
        existing_sketch.deleteMe()
    face = side_face(body, x_cm, normal_sign)
    sketch = root.sketches.add(face)
    sketch.name = f'05_{side}拎带孔及加强台草图'
    center = sketch.modelToSketchSpace(adsk.core.Point3D.create(x_cm, 13.0, 3.5))
    outer = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 0.9)
    inner = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 0.45)

    outer_dim = sketch.sketchDimensions.addDiameterDimension(
        outer, sketch.modelToSketchSpace(adsk.core.Point3D.create(x_cm, 14.5, 5.0))
    )
    outer_dim.parameter.expression = 'HandleHoleD + 2 * HandleBossRadial'
    inner_dim = sketch.sketchDimensions.addDiameterDimension(
        inner, sketch.modelToSketchSpace(adsk.core.Point3D.create(x_cm, 11.5, 5.0))
    )
    inner_dim.parameter.expression = 'HandleHoleD'

    ring_profiles = []
    for profile in sketch.profiles:
        if profile.profileLoops.count != 2:
            continue
        size_x, size_y = profile_xy_size(profile)
        if abs(size_x - 1.8) < 0.001 and abs(size_y - 1.8) < 0.001:
            ring_profiles.append(profile)
    if len(ring_profiles) != 1:
        raise RuntimeError(f'{side}侧加强台圆环轮廓数量异常: {len(ring_profiles)}')
    before_boss = body.volume
    boss_input = root.features.extrudeFeatures.createInput(
        ring_profiles[0], adsk.fusion.FeatureOperations.JoinFeatureOperation
    )
    boss_extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('HandleBossT')
    )
    if not boss_input.setOneSideExtent(
        boss_extent, adsk.fusion.ExtentDirections.PositiveExtentDirection,
        adsk.core.ValueInput.createByString('0 deg')
    ):
        raise RuntimeError(f'{side}侧加强台拉伸范围设置失败')
    boss = root.features.extrudeFeatures.add(boss_input)
    boss.name = f'05_{side}拎带加强台_径向4.5_厚4.5mm'
    boss_delta = body.volume - before_boss
    expected_boss = math.pi * (0.9 ** 2 - 0.45 ** 2) * 0.45
    if abs(boss_delta - expected_boss) > 0.005:
        raise RuntimeError(
            f'{side}侧加强台体积异常: 实际 {boss_delta:.6f}, 预期 {expected_boss:.6f} cm^3'
        )

    hole_profiles = []
    for profile in sketch.profiles:
        if profile.profileLoops.count != 1:
            continue
        size_x, size_y = profile_xy_size(profile)
        if abs(size_x - 0.9) < 0.001 and abs(size_y - 0.9) < 0.001:
            hole_profiles.append(profile)
    if len(hole_profiles) != 1:
        raise RuntimeError(f'{side}侧拎带孔轮廓数量异常: {len(hole_profiles)}')
    before_hole = body.volume
    hole_input = root.features.extrudeFeatures.createInput(
        hole_profiles[0], adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    # 草图位于侧壁外表面；加强台已经是环形，仅需切除 2.2 mm 侧壁。
    hole_extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('WallT')
    )
    if not hole_input.setOneSideExtent(
        hole_extent, adsk.fusion.ExtentDirections.NegativeExtentDirection,
        adsk.core.ValueInput.createByString('0 deg')
    ):
        raise RuntimeError(f'{side}侧拎带孔切除范围设置失败')
    hole = root.features.extrudeFeatures.add(hole_input)
    hole.name = f'05_{side}拎带孔_Ø9mm'
    hole_delta = before_hole - body.volume
    expected_hole = math.pi * 0.45 ** 2 * 0.22
    if abs(hole_delta - expected_hole) > 0.005:
        raise RuntimeError(
            f'{side}侧拎带孔切除体积异常: 实际 {hole_delta:.6f}, 预期 {expected_hole:.6f} cm^3'
        )
    results.append({'side': side, 'boss_volume_cm3': boss_delta,
                    'wall_hole_volume_cm3': hole_delta,
                    'boss_feature': boss.name, 'hole_feature': hole.name})

if root.bRepBodies.count != 1:
    raise RuntimeError('步骤5完成后实体数量不为1')
print({'step': 5, 'hole_diameter_mm': 9.0, 'boss_outer_diameter_mm': 18.0,
       'boss_radial_mm': 4.5, 'boss_thickness_mm': 4.5,
       'center_y_mm': 130.0, 'center_z_mm': 35.0,
       'results': results, 'body_count': root.bRepBodies.count})
