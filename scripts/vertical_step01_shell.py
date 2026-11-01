app = adsk.core.Application.get()
old_doc = app.activeDocument
if old_doc and not old_doc.isSaved:
    if not old_doc.save('开始竖向新版前保留上一版模型'):
        raise RuntimeError('上一文档未保存，步骤1停止以避免丢失')

new_doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
design = adsk.fusion.Design.cast(app.activeProduct)
if design is None:
    raise RuntimeError('未能创建 Fusion Design 文档')
if design.unitsManager.defaultLengthUnits != 'mm':
    raise RuntimeError('新文档单位不是 mm，步骤1停止')
design.designType = adsk.fusion.DesignTypes.ParametricDesignType
root = design.rootComponent


def set_parameter(name, expression):
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(
            name, adsk.core.ValueInput.createByString(expression), 'mm', name
        )


for name, expression in {
    'OuterL': '300 mm', 'OuterD': '210 mm', 'OuterH': '210 mm',
    'WallT': '2.2 mm', 'OuterR': '3 mm', 'FitClearance': '0.75 mm',
    'DividerRootR': '2 mm', 'GridGap': '4 mm', 'GridRib': '2.2 mm',
    'FootH': '5 mm', 'CableSlotW': '10 mm', 'HandleHoleD': '9 mm',
    'HandleBossT': '4.5 mm', 'HandleBossRadial': '4.5 mm', 'VentMargin': '8 mm',
}.items():
    set_parameter(name, expression)

sketch = root.sketches.add(root.xYConstructionPlane)
sketch.name = '01_外框轮廓_300x210mm'
lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(30, 21, 0)
)
sketch.geometricConstraints.addCoincident(lines.item(0).startSketchPoint, sketch.originPoint)
length_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(0).startSketchPoint, lines.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    adsk.core.Point3D.create(15, -2, 0)
)
length_dim.parameter.expression = 'OuterL'
depth_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(1).startSketchPoint, lines.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    adsk.core.Point3D.create(32, 10.5, 0)
)
depth_dim.parameter.expression = 'OuterD'

extrude_input = root.features.extrudeFeatures.createInput(
    sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('OuterH')
)
if not extrude_input.setOneSideExtent(
    extent, adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
):
    raise RuntimeError('外框单侧拉伸设置失败')
base = root.features.extrudeFeatures.add(extrude_input)
base.name = '01_外框基体_高210mm'
body = base.bodies.item(0)
body.name = '01_竖向收纳盒壳体'

outer_edges = adsk.core.ObjectCollection.create()
for edge in body.edges:
    outer_edges.add(edge)
if outer_edges.count != 12:
    raise RuntimeError(f'外框基体边线数量异常: {outer_edges.count}')
fillet_input = root.features.filletFeatures.createInput()
fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
    outer_edges, adsk.core.ValueInput.createByString('OuterR'), False
)
outer_fillet = root.features.filletFeatures.add(fillet_input)
outer_fillet.name = '01_壳体外轮廓边角_R3'

# 外轮廓圆角后再抽壳，顶面只保留一个平面轮廓。
top_faces = adsk.core.ObjectCollection.create()
for face in body.faces:
    plane = adsk.core.Plane.cast(face.geometry)
    if (plane and plane.normal.z > 0.999 and
            abs(face.boundingBox.minPoint.z - 21.0) < 0.001 and
            abs(face.boundingBox.maxPoint.z - 21.0) < 0.001):
        top_faces.add(face)
if top_faces.count != 1:
    raise RuntimeError(f'顶部抽壳面数量异常: {top_faces.count}')
shell_input = root.features.shellFeatures.createInput(top_faces, False)
shell_input.insideThickness = adsk.core.ValueInput.createByString('WallT')
shell = root.features.shellFeatures.add(shell_input)
shell.name = '01_顶部开口_壁厚2.2mm'

bbox = body.boundingBox
size_mm = [(bbox.maxPoint.x - bbox.minPoint.x) * 10,
           (bbox.maxPoint.y - bbox.minPoint.y) * 10,
           (bbox.maxPoint.z - bbox.minPoint.z) * 10]
if any(abs(actual - expected) > 0.01 for actual, expected in zip(size_mm, [300, 210, 210])):
    raise RuntimeError(f'外框包围盒异常: {size_mm}')
if root.bRepBodies.count != 1:
    raise RuntimeError('步骤1完成后实体数量不为1')

inner_bottom_faces = []
for face in body.faces:
    plane = adsk.core.Plane.cast(face.geometry)
    if plane and abs(plane.normal.z) > 0.999 and abs(face.boundingBox.minPoint.z - 0.22) < 0.001:
        inner_bottom_faces.append(face)
if not inner_bottom_faces:
    raise RuntimeError('未找到 Z=2.2 mm 的内底面，底厚自检失败')

print({'step': 1, 'size_mm': size_mm, 'wall_mm': 2.2, 'outer_radius_mm': 3.0,
       'rounded_edge_count': outer_edges.count, 'inner_bottom_z_mm': 2.2,
       'body_count': root.bRepBodies.count,
       'features': [base.name, outer_fillet.name, shell.name]})
