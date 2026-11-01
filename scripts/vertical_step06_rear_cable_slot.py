design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤6要求当前为单一实体')
feature_name = '06_后上沿贯通出线槽_宽10mm'
if root.features.extrudeFeatures.itemByName(feature_name):
    raise RuntimeError('后上沿出线槽已存在，停止以避免重复切除')
parameter = design.userParameters.itemByName('RearCableSlotW')
if parameter is None:
    design.userParameters.add(
        'RearCableSlotW', adsk.core.ValueInput.createByString('10 mm'), 'mm',
        '后上沿贯通出线槽向下宽度'
    )
else:
    parameter.expression = '10 mm'

plane_input = root.constructionPlanes.createInput()
plane_input.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByString('OuterH'))
plane = root.constructionPlanes.add(plane_input)
plane.name = '06_后上沿草图平面_Z210mm'
sketch = root.sketches.add(plane)
sketch.name = '06_草图_后上沿贯通出线槽_宽10mm'
sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0.22, 20.78, 0),
    adsk.core.Point3D.create(29.78, 21.0, 0)
)
if sketch.profiles.count != 1:
    raise RuntimeError(f'出线槽轮廓数量异常: {sketch.profiles.count}')
cut_input = root.features.extrudeFeatures.createInput(
    sketch.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
cut_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString('RearCableSlotW')),
    adsk.fusion.ExtentDirections.NegativeExtentDirection,
    adsk.core.ValueInput.createByString('0 deg'))
slot = root.features.extrudeFeatures.add(cut_input)
slot.name = feature_name

bottom_faces = []
for face in body.faces:
    if not adsk.core.Plane.cast(face.geometry):
        continue
    box = face.boundingBox
    if (abs(box.minPoint.z-20.0) < 0.001 and abs(box.maxPoint.z-20.0) < 0.001
            and abs(box.minPoint.x-0.22) < 0.001 and abs(box.maxPoint.x-29.78) < 0.001
            and abs(box.minPoint.y-20.78) < 0.001 and abs(box.maxPoint.y-21.0) < 0.001):
        bottom_faces.append(face)
non_manifold_count = sum(1 for edge in body.edges if edge.faces.count > 2)
if len(bottom_faces) != 1:
    raise RuntimeError(f'出线槽底面数量或尺寸异常: {len(bottom_faces)}')
if root.bRepBodies.count != 1 or non_manifold_count:
    raise RuntimeError('出线槽完成后存在多实体或非流形边')
print({'step': 6, 'slot_vertical_width_mm': 10.0,
       'slot_horizontal_span_mm': 295.6, 'z_bounds_mm': [200.0, 210.0],
       'x_bounds_mm': [2.2, 297.8], 'y_bounds_mm': [207.8, 210.0],
       'remaining_web_above_back_grille_mm': 2.2,
       'body_count': 1, 'non_manifold_edge_count': non_manifold_count,
       'feature': slot.name})
