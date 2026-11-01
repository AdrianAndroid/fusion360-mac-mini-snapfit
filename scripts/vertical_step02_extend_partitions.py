design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
names = [
    '02_草图_主隔板1_Mac与3.5硬盘_厚2.2mm',
    '02_草图_主隔板2_3.5与2.5硬盘_厚2.2mm',
    '02_草图_主隔板3_2.5硬盘与Hub_厚2.2mm',
]
for name in names:
    sketch = root.sketches.itemByName(name)
    if sketch is None:
        raise RuntimeError('找不到主隔板草图: ' + name)
    if sketch.sketchDimensions.count != 2:
        raise RuntimeError('主隔板草图尺寸数量异常: ' + name)
    sketch.sketchDimensions.item(1).parameter.expression = '200.65 mm'

body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
partition_x = [38.75, 40.95, 67.8, 70.0, 80.25, 82.45]
stop_y = [200.65, 202.85, 104.55, 106.75, 72.8, 75.0, 107.95, 110.15]
selected = []
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
        selected.append({'cx': round(cx, 3), 'cy': round(cy, 3),
                         'dx': round(dx, 3), 'dy': round(dy, 3)})
print({'updated_partition_depth_mm': 200.65, 'rear_wiring_gap_mm': 4.95,
       'selected_root_count': len(selected), 'selected_roots': selected})
