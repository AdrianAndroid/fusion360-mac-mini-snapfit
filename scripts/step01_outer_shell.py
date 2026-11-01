app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
if design is None:
    raise RuntimeError('当前没有激活的 Fusion Design 文档')
if design.rootComponent.bRepBodies.count != 0:
    raise RuntimeError('当前文档已有实体，步骤1停止以避免覆盖既有模型')

design.designType = adsk.fusion.DesignTypes.ParametricDesignType
if design.unitsManager.defaultLengthUnits != 'mm':
    raise RuntimeError('当前文档单位不是 mm，已停止建模')
root = design.rootComponent


def set_parameter(name, expression, unit='mm'):
    parameter = design.userParameters.itemByName(name)
    if parameter:
        parameter.expression = expression
    else:
        design.userParameters.add(
            name, adsk.core.ValueInput.createByString(expression), unit, name
        )


set_parameter('OuterL', '390 mm')
set_parameter('OuterW', '260 mm')
set_parameter('OuterH', '70 mm')
set_parameter('WallT', '2.2 mm')
set_parameter('FitClearance', '0.75 mm')
set_parameter('DividerRootR', '2 mm')
set_parameter('GridGap', '4 mm')
set_parameter('GridRib', '2.2 mm')
set_parameter('CableSlotW', '10 mm')
set_parameter('HandleHoleD', '9 mm')
set_parameter('HandleBossT', '4.5 mm')
set_parameter('VentMargin', '8 mm')

sketch = root.sketches.itemByName('01_外框轮廓_390x260mm')
if sketch:
    sketch.deleteMe()
sketch = root.sketches.add(root.xYConstructionPlane)
sketch.name = '01_外框轮廓_390x260mm'
lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(39, 26, 0)
)
sketch.geometricConstraints.addCoincident(lines.item(0).startSketchPoint, sketch.originPoint)
length_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(0).startSketchPoint,
    lines.item(0).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    adsk.core.Point3D.create(19.5, -2, 0)
)
length_dim.parameter.expression = 'OuterL'
width_dim = sketch.sketchDimensions.addDistanceDimension(
    lines.item(1).startSketchPoint,
    lines.item(1).endSketchPoint,
    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
    adsk.core.Point3D.create(41, 13, 0)
)
width_dim.parameter.expression = 'OuterW'

profile = sketch.profiles.item(0)
extrudes = root.features.extrudeFeatures
extrude_input = extrudes.createInput(
    profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
extent = adsk.fusion.DistanceExtentDefinition.create(
    adsk.core.ValueInput.createByString('OuterH')
)
extrude_input.setOneSideExtent(
    extent,
    adsk.fusion.ExtentDirections.PositiveExtentDirection,
    adsk.core.ValueInput.createByString('0 deg')
)
base = extrudes.add(extrude_input)
base.name = '01_外框基体_高70mm'
body = base.bodies.item(0)
body.name = '01_外框壳体'

top_faces = adsk.core.ObjectCollection.create()
for face in body.faces:
    plane = adsk.core.Plane.cast(face.geometry)
    if plane and abs(plane.normal.z) > 0.999:
        if abs(face.boundingBox.maxPoint.z - 7.0) < 0.0001:
            top_faces.add(face)
if top_faces.count != 1:
    raise RuntimeError(f'顶面数量异常: {top_faces.count}')

shell_input = root.features.shellFeatures.createInput(top_faces, False)
shell_input.insideThickness = adsk.core.ValueInput.createByString('WallT')
shell = root.features.shellFeatures.add(shell_input)
shell.name = '01_顶部开口_壁厚2.2mm'

bbox = body.boundingBox
print({
    'step': 1,
    'body_count': root.bRepBodies.count,
    'body_name': body.name,
    'bbox_mm': [39 * 10, 26 * 10, 7 * 10],
    'actual_bbox_cm': [bbox.maxPoint.x - bbox.minPoint.x,
                       bbox.maxPoint.y - bbox.minPoint.y,
                       bbox.maxPoint.z - bbox.minPoint.z],
    'features': [base.name, shell.name],
    'parameters_mm': {'OuterL': 390, 'OuterW': 260, 'OuterH': 70, 'WallT': 2.2}
})
