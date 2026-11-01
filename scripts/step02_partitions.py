design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤2要求当前只有外框壳体实体')


def set_parameter(name, expression):
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(
            name, adsk.core.ValueInput.createByString(expression), 'mm', name
        )


for name, value in {
    'MacSlotL': '198.45 mm', 'MacSlotW': '198.45 mm', 'MacSlotH': '36.55 mm',
    'HDD35SlotL': '102.35 mm', 'HDD35SlotW': '146.75 mm', 'HDD35SlotH': '26.85 mm',
    'HDD25SlotL': '100.75 mm', 'HDD25SlotW': '70.6 mm', 'HDD25SlotH': '10.25 mm',
    'PowerSlotL': '75.75 mm', 'PowerSlotW': '220.75 mm', 'PowerSlotH': '32.75 mm',
}.items():
    set_parameter(name, value)


def add_dimension(sketch, point_one, point_two, orientation, text_point, expression):
    dim = sketch.sketchDimensions.addDistanceDimension(
        point_one, point_two, orientation, text_point
    )
    dim.parameter.expression = expression


created = []


def make_wall(label, x1, y1, x2, y2, slot_height):
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = '02_草图_' + label
    lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(x1 / 10, y1 / 10, 0),
        adsk.core.Point3D.create(x2 / 10, y2 / 10, 0)
    )
    start = lines.item(0).startSketchPoint
    add_dimension(sketch, sketch.originPoint, start,
                  adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                  adsk.core.Point3D.create(x1 / 20, (y1 - 8) / 10, 0), f'{x1} mm')
    add_dimension(sketch, sketch.originPoint, start,
                  adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                  adsk.core.Point3D.create((x1 - 8) / 10, y1 / 20, 0), f'{y1} mm')
    add_dimension(sketch, lines.item(0).startSketchPoint, lines.item(0).endSketchPoint,
                  adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                  adsk.core.Point3D.create((x1 + x2) / 20, (y1 - 4) / 10, 0), f'{x2-x1} mm')
    add_dimension(sketch, lines.item(1).startSketchPoint, lines.item(1).endSketchPoint,
                  adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                  adsk.core.Point3D.create((x2 + 4) / 10, (y1 + y2) / 20, 0), f'{y2-y1} mm')
    extrude_input = root.features.extrudeFeatures.createInput(
        sketch.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation
    )
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString(f'{slot_height + 2.2} mm')
    )
    if not extrude_input.setOneSideExtent(
        extent, adsk.fusion.ExtentDirections.PositiveExtentDirection,
        adsk.core.ValueInput.createByString('0 deg')
    ):
        raise RuntimeError('隔板拉伸范围设置失败: ' + label)
    feature = root.features.extrudeFeatures.add(extrude_input)
    feature.name = '02_隔板_' + label + '_厚2.2mm'
    created.append(feature.name)


# 所有坐标均为 mm；隔板从 Z=0 与底板合并，仓高从底板上表面 Z=2.2 起算。
make_wall('Mac右前_3.5左', 200.65, 2.2, 202.85, 151.15, 36.55)
make_wall('Mac右后_2.5左', 202.25, 151.15, 204.45, 257.8, 36.55)
make_wall('Mac后挡', 2.2, 200.65, 204.45, 202.85, 36.55)
make_wall('硬盘仓间断', 200.65, 148.95, 307.4, 151.15, 26.85)
make_wall('硬盘右_插排左', 305.2, 2.2, 307.4, 257.8, 32.75)
make_wall('2.5后挡', 204.45, 221.75, 305.2, 223.95, 10.25)
make_wall('插排后挡', 307.4, 222.95, 385.35, 225.15, 32.75)
make_wall('插排右_走线槽左', 383.15, 2.2, 385.35, 225.15, 32.75)

body = root.bRepBodies.itemByName('01_外框壳体')
if body is None:
    body = root.bRepBodies.item(0)
    body.name = '01_外框壳体'

edges = adsk.core.ObjectCollection.create()
for edge in body.edges:
    if not adsk.core.Line3D.cast(edge.geometry):
        continue
    bbox = edge.boundingBox
    if abs(bbox.minPoint.z - 0.22) > 0.0001 or abs(bbox.maxPoint.z - 0.22) > 0.0001:
        continue
    if edge.length < 2.0:
        continue
    cx = (bbox.minPoint.x + bbox.maxPoint.x) / 2
    cy = (bbox.minPoint.y + bbox.maxPoint.y) / 2
    on_outer = any([
        abs(cx - 0.22) < 0.001, abs(cx - 38.78) < 0.001,
        abs(cy - 0.22) < 0.001, abs(cy - 25.78) < 0.001,
    ])
    if not on_outer:
        edges.add(edge)

if edges.count == 0:
    raise RuntimeError('未找到隔板根部边线')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    edges, adsk.core.ValueInput.createByString('DividerRootR'), False
)
fillet = root.features.filletFeatures.add(fillet_input)
fillet.name = '02_隔板根部圆角_R2'

slots = {
    'Mac_mini': [198.45, 198.45, 36.55],
    'HDD_3.5': [102.35, 146.75, 26.85],
    'HDD_2.5': [100.75, 70.6, 10.25],
    'Power_strip': [75.75, 220.75, 32.75],
}
print({'step': 2, 'created_features': created + [fillet.name],
       'fillet_edge_count': edges.count, 'slots_mm': slots,
       'body_count': root.bRepBodies.count})
