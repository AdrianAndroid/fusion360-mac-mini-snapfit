design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
sketch = root.sketches.itemByName('03_草图_支撑脚环形截面_壁厚2.2mm')
foot = root.features.extrudeFeatures.itemByName('03_支撑脚_高5mm_壁厚2.2mm')
if sketch is None or foot is None:
    raise RuntimeError('找不到待修正的支撑脚草图或特征')
parameter = design.userParameters.itemByName('FootJoinOverlap')
if parameter is None:
    design.userParameters.add(
        'FootJoinOverlap', adsk.core.ValueInput.createByString('0.1 mm'), 'mm',
        '支撑脚与壳底的实体搭接量，外部抬高仍为5mm'
    )
else:
    parameter.expression = '0.1 mm'
foot.startExtent = adsk.fusion.OffsetStartDefinition.create(
    adsk.core.ValueInput.createByString('FootJoinOverlap')
)
foot.extentOne = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('FootH + FootJoinOverlap')
)
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
non_manifold = []
for edge in body.edges:
    if edge.faces.count > 2:
        box = edge.boundingBox
        non_manifold.append({'faces': edge.faces.count,
                             'min_mm': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                             'max_mm': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]})
print({'overlap_mm': 0.1, 'body_count': root.bRepBodies.count,
       'non_manifold_edge_count': len(non_manifold),
       'non_manifold_edges': non_manifold,
       'foot_error': foot.errorOrWarningMessage})
if root.bRepBodies.count != 1 or non_manifold:
    raise RuntimeError('支撑脚搭接修正后仍存在实体或非流形异常，停止根部圆角')
