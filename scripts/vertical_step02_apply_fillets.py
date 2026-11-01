design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
root_edges = adsk.core.ObjectCollection.create()
partition_x = [38.75, 40.95, 67.8, 70.0, 80.25, 82.45]
stop_y = [200.65, 202.85, 104.55, 106.75, 72.8, 75.0, 107.95, 110.15]
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    box = edge.boundingBox
    if abs(box.minPoint.z - 0.22) > 0.001 or abs(box.maxPoint.z - 0.22) > 0.001:
        continue
    dx = (box.maxPoint.x - box.minPoint.x) * 10
    dy = (box.maxPoint.y - box.minPoint.y) * 10
    cx = (box.minPoint.x + box.maxPoint.x) * 5
    cy = (box.minPoint.y + box.maxPoint.y) * 5
    is_partition_root = dx < 0.01 and dy > 3.0 and any(abs(cx - x) < 0.01 for x in partition_x)
    is_stop_root = dy < 0.01 and dx > 10.0 and any(abs(cy - y) < 0.01 for y in stop_y)
    if is_partition_root or is_stop_root:
        root_edges.add(edge)
if root_edges.count != 19:
    raise RuntimeError(f'修正后隔板根边数量异常: {root_edges.count}，预期19')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    root_edges, adsk.core.ValueInput.createByString('DividerRootR'), False
)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '02_隔板与限位筋根部圆角_R2'
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤2圆角后实体数量不为1')
print({'step': 2, 'corrected': True, 'root_fillet_edges': root_edges.count,
       'fillet_feature': fillet.name, 'body_count': root.bRepBodies.count})
