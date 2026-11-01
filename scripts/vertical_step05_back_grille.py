design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤5要求当前为单一实体')
feature_name = '05_后背板竖向格栅_47缝4mm_筋2.2mm'
if root.features.extrudeFeatures.itemByName(feature_name):
    raise RuntimeError('后背板格栅已存在，停止以避免重复切除')
for name, expression in {'BackSlotW': '4 mm', 'BackRibW': '2.2 mm'}.items():
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(name, adsk.core.ValueInput.createByString(expression), 'mm', name)

back_faces = []
for face in body.faces:
    if not adsk.core.Plane.cast(face.geometry):
        continue
    box = face.boundingBox
    if (abs(box.minPoint.y - 21.0) < 0.001 and abs(box.maxPoint.y - 21.0) < 0.001
            and (box.maxPoint.x-box.minPoint.x)*10 > 200
            and (box.maxPoint.z-box.minPoint.z)*10 > 200):
        back_faces.append(face)
if len(back_faces) != 1:
    raise RuntimeError(f'后背板外平面数量异常: {len(back_faces)}')
existing_sketch = root.sketches.itemByName('05_草图_后背板竖向格栅_缝4mm_筋2.2mm')
if existing_sketch:
    existing_sketch.deleteMe()
sketch = root.sketches.add(back_faces[0])
sketch.name = '05_草图_后背板竖向格栅_缝4mm_筋2.2mm'
inverse = sketch.transform.copy()
if not inverse.invert():
    raise RuntimeError('后背板草图坐标逆变换失败')

slot_count = 47
pitch = 6.2
occupied = slot_count * 4.0 + (slot_count - 1) * 2.2
x_start = 4.4 + ((295.6 - 4.4) - occupied) / 2
z_bottom, z_top = 4.4, 197.8
for index in range(slot_count):
    x1 = x_start + index * pitch
    point_one = adsk.core.Point3D.create(x1/10, 21.0, z_bottom/10)
    point_two = adsk.core.Point3D.create((x1+4.0)/10, 21.0, z_top/10)
    point_one.transformBy(inverse)
    point_two.transformBy(inverse)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point_one, point_two)
profiles = adsk.core.ObjectCollection.create()
for profile in sketch.profiles:
    box = profile.boundingBox
    dimensions = sorted([(box.maxPoint.x-box.minPoint.x)*10,
                         (box.maxPoint.y-box.minPoint.y)*10])
    if abs(dimensions[0]-4.0) < 0.01 and abs(dimensions[1]-(z_top-z_bottom)) < 0.01:
        profiles.add(profile)
if profiles.count != slot_count:
    raise RuntimeError(f'后背板格栅轮廓数量异常: {profiles.count}，预期{slot_count}')
cut_input = root.features.extrudeFeatures.createInput(
    profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
cut_input.setTwoSidesExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.core.ValueInput.createByString('0 deg'),
    adsk.core.ValueInput.createByString('0 deg'))
grille = root.features.extrudeFeatures.add(cut_input)
grille.name = feature_name

non_manifold_count = sum(1 for edge in body.edges if edge.faces.count > 2)
box = body.boundingBox
if root.bRepBodies.count != 1 or non_manifold_count:
    raise RuntimeError('后背板格栅完成后存在多实体或非流形边')
if abs(box.minPoint.y) > 0.01 or abs(box.maxPoint.y*10-210) > 0.01:
    raise RuntimeError('后背板格栅切深了，外框Y尺寸异常')
print({'step': 5, 'slot_count': slot_count, 'slot_width_mm': 4.0,
       'rib_width_mm': 2.2, 'pitch_mm': pitch,
       'slot_height_mm': z_top-z_bottom, 'z_bounds_mm': [z_bottom, z_top],
       'first_slot_x_mm': x_start, 'last_slot_end_x_mm': x_start+46*pitch+4.0,
       'cut_depth_mm': 2.2, 'body_count': 1,
       'non_manifold_edge_count': non_manifold_count, 'feature': grille.name})
