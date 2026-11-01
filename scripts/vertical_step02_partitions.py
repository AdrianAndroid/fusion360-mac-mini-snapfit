design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None or root.bRepBodies.count != 1:
    raise RuntimeError('步骤2要求当前只有新版外壳单一实体')


def set_parameter(name, expression):
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(
            name, adsk.core.ValueInput.createByString(expression), 'mm', name
        )


for name, expression in {
    'MacSlotW': '36.55 mm', 'MacSlotD': '198.45 mm', 'MacSlotH': '198.45 mm',
    'HDD35SlotW': '26.85 mm', 'HDD35SlotD': '102.35 mm', 'HDD35SlotH': '146.75 mm',
    'HDD25SlotW': '10.25 mm', 'HDD25SlotD': '70.6 mm', 'HDD25SlotH': '100.75 mm',
    'HubSlotW': '32.75 mm', 'HubSlotD': '105.75 mm', 'HubSlotH': '120.75 mm',
    'CableChannelW': '182.6 mm',
}.items():
    set_parameter(name, expression)

created = []


def make_xy_prism(label, x1, y1, x2, y2, height_expression):
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = '02_草图_' + label
    lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(x1 / 10, y1 / 10, 0),
        adsk.core.Point3D.create(x2 / 10, y2 / 10, 0)
    )
    width_dim = sketch.sketchDimensions.addDistanceDimension(
        lines.item(0).startSketchPoint, lines.item(0).endSketchPoint,
        adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
        adsk.core.Point3D.create((x1 + x2) / 20, (y1 - 5) / 10, 0)
    )
    width_dim.parameter.expression = f'{x2-x1:.4f} mm'
    depth_dim = sketch.sketchDimensions.addDistanceDimension(
        lines.item(1).startSketchPoint, lines.item(1).endSketchPoint,
        adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
        adsk.core.Point3D.create((x2 + 5) / 10, (y1 + y2) / 20, 0)
    )
    depth_dim.parameter.expression = f'{y2-y1:.4f} mm'
    extrude_input = root.features.extrudeFeatures.createInput(
        sketch.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation
    )
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString(height_expression)
    )
    if not extrude_input.setOneSideExtent(
        extent, adsk.fusion.ExtentDirections.PositiveExtentDirection,
        adsk.core.ValueInput.createByString('0 deg')
    ):
        raise RuntimeError('拉伸范围设置失败: ' + label)
    feature = root.features.extrudeFeatures.add(extrude_input)
    feature.name = '02_' + label
    created.append(feature.name)


# 主隔板全高，延伸至 Mac 后限位筋背面 Y=202.85，确保面接触；距背板内壁 4.95 mm。
make_xy_prism('主隔板1_Mac与3.5硬盘_厚2.2mm', 38.75, 2.2, 40.95, 202.85, 'OuterH')
make_xy_prism('主隔板2_3.5与2.5硬盘_厚2.2mm', 67.8, 2.2, 70.0, 202.85, 'OuterH')
make_xy_prism('主隔板3_2.5硬盘与Hub_厚2.2mm', 80.25, 2.2, 82.45, 202.85, 'OuterH')

# 后限位筋厚 2.2 mm；顶面高度=内底面 2.2+设备净高，以上形成走线空间。
make_xy_prism('Mac后限位筋_净深198.45mm', 2.2, 200.65, 38.75, 202.85, 'MacSlotH + WallT')
make_xy_prism('3.5硬盘后限位筋_净深102.35mm', 40.95, 104.55, 67.8, 106.75, 'HDD35SlotH + WallT')
make_xy_prism('2.5硬盘后限位筋_净深70.6mm', 70.0, 72.8, 80.25, 75.0, 'HDD25SlotH + WallT')
make_xy_prism('Hub后限位筋_净深105.75mm', 82.45, 107.95, 115.2, 110.15, 'HubSlotH + WallT')

# 选择主隔板分段根边与后限位筋长根边，共19条。
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
    raise RuntimeError(f'隔板根边数量异常: {root_edges.count}，预期19')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    root_edges, adsk.core.ValueInput.createByString('DividerRootR'), False
)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '02_隔板与限位筋根部圆角_R2'
created.append(fillet.name)

slots = {
    'Mac mini': [36.55, 198.45, 198.45],
    '3.5寸硬盘': [26.85, 102.35, 146.75],
    '2.5寸硬盘': [10.25, 70.6, 100.75],
    'Upstone Hub': [32.75, 105.75, 120.75],
}
# 坐标差自检：净宽、净深和右侧走线通道。
if abs((38.75 - 2.2) - 36.55) > 0.001 or abs((67.8 - 40.95) - 26.85) > 0.001:
    raise RuntimeError('Mac或3.5寸仓位净宽自检失败')
if abs((80.25 - 70.0) - 10.25) > 0.001 or abs((115.2 - 82.45) - 32.75) > 0.001:
    raise RuntimeError('2.5寸或Hub仓位净宽自检失败')
if abs((297.8 - 115.2) - 182.6) > 0.001:
    raise RuntimeError('右侧走线通道宽度自检失败')
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤2完成后实体数量不为1')
print({'step': 2, 'slots_mm': slots, 'cable_channel_width_mm': 182.6,
       'main_partition_height_mm': 210.0, 'rear_wiring_gap_mm': 4.95,
       'root_fillet_edges': root_edges.count, 'features': created,
       'body_count': root.bRepBodies.count})
