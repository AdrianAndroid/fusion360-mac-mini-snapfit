design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤3收尾要求单一实体')
if root.features.extrudeFeatures.itemByName('03_底部横向格栅_32缝4mm_筋2.2mm'):
    raise RuntimeError('底部格栅已存在，停止以避免重复切除')
if any(edge.faces.count > 2 for edge in body.edges):
    raise RuntimeError('根部圆角前检测到非流形边，停止')

# 支撑脚为周边脚壁而非隔板/格栅筋；不保留无法生成的根部R2失败特征。
existing_sketch = root.sketches.itemByName('03_草图_底部横向格栅_缝4mm_筋2.2mm')
if existing_sketch:
    existing_sketch.deleteMe()
sketch = root.sketches.add(root.xYConstructionPlane)
sketch.name = '03_草图_底部横向格栅_缝4mm_筋2.2mm'
slot_count = 32
pitch = 6.2
occupied = slot_count * 4.0 + (slot_count - 1) * 2.2
y_start = 4.4 + ((205.6 - 4.4) - occupied) / 2
for index in range(slot_count):
    y1 = y_start + index * pitch
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0.44, y1 / 10, 0),
        adsk.core.Point3D.create(29.56, (y1 + 4.0) / 10, 0)
    )
if sketch.profiles.count != slot_count:
    raise RuntimeError(f'底部格栅轮廓数量异常: {sketch.profiles.count}')
profiles = adsk.core.ObjectCollection.create()
for profile in sketch.profiles:
    profiles.add(profile)
cut_input = root.features.extrudeFeatures.createInput(
    profiles, adsk.fusion.FeatureOperations.CutFeatureOperation
)
cut_input.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('WallT')),
    adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
)
grille = root.features.extrudeFeatures.add(cut_input)
grille.name = '03_底部横向格栅_32缝4mm_筋2.2mm'

non_manifold_count = sum(1 for edge in body.edges if edge.faces.count > 2)
box = body.boundingBox
size_mm = [(box.maxPoint.x - box.minPoint.x) * 10,
           (box.maxPoint.y - box.minPoint.y) * 10,
           (box.maxPoint.z - box.minPoint.z) * 10]
if abs(box.minPoint.z * 10 + 5.0) > 0.01 or abs(box.maxPoint.z * 10 - 210.0) > 0.01:
    raise RuntimeError('步骤3 Z向包围盒异常')
if abs(size_mm[0] - 300) > 0.01 or abs(size_mm[1] - 210) > 0.01:
    raise RuntimeError('步骤3外轮廓尺寸异常')
if root.bRepBodies.count != 1 or non_manifold_count:
    raise RuntimeError('步骤3完成后存在多实体或非流形边')
print({'step': 3, 'corrected': True, 'body_count': root.bRepBodies.count,
       'non_manifold_edge_count': non_manifold_count,
       'bbox_size_mm': size_mm, 'z_range_mm': [box.minPoint.z*10, box.maxPoint.z*10],
       'visible_foot_height_mm': 5.0, 'join_overlap_mm': 0.1,
       'foot_wall_mm': 2.2, 'slot_count': slot_count,
       'slot_width_mm': 4.0, 'rib_width_mm': 2.2, 'pitch_mm': pitch,
       'first_slot_y_mm': y_start, 'last_slot_end_y_mm': y_start + 31*pitch + 4.0,
       'features': ['03_支撑脚_高5mm_壁厚2.2mm', '03_支撑脚外竖角_R3', grille.name]})
