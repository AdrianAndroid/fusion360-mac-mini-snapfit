app = adsk.core.Application.get()
doc = app.activeDocument
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
body = root.bRepBodies.itemByName('01_竖向收纳盒壳体')
if body is None:
    raise RuntimeError('最终自检找不到主实体')
front_faces = []
for face in body.faces:
    if not adsk.core.Plane.cast(face.geometry):
        continue
    box = face.boundingBox
    if (abs(box.minPoint.y) < 0.001 and abs(box.maxPoint.y) < 0.001
            and (box.maxPoint.x-box.minPoint.x)*10 > 200
            and (box.maxPoint.z-box.minPoint.z)*10 > 200):
        front_faces.append(face)
feature_errors = []
for collection in (root.features.extrudeFeatures, root.features.filletFeatures, root.features.shellFeatures):
    for feature in collection:
        message = feature.errorOrWarningMessage
        if message:
            feature_errors.append({'feature': feature.name, 'message': message})
box = body.boundingBox
non_manifold_count = sum(1 for edge in body.edges if edge.faces.count > 2)
parameters = {p.name: p.expression for p in design.userParameters}
required_parameters = [
    'OuterL', 'OuterD', 'OuterH', 'WallT', 'OuterR', 'DividerRootR',
    'MacSlotW', 'MacSlotD', 'MacSlotH', 'HDD35SlotW', 'HDD35SlotD', 'HDD35SlotH',
    'HDD25SlotW', 'HDD25SlotD', 'HDD25SlotH', 'HubSlotW', 'HubSlotD', 'HubSlotH',
    'FootH', 'FootWallT', 'BottomSlotW', 'BottomRibW', 'MacVentBorder',
    'BackSlotW', 'BackRibW', 'RearCableSlotW', 'HandleHoleD', 'HandleRadialW', 'HandleBossT'
]
missing = [name for name in required_parameters if name not in parameters]
result = {
    'document': doc.name, 'native_saved': doc.isSaved,
    'design_type': str(design.designType), 'document_units': design.unitsManager.defaultLengthUnits,
    'body_count': root.bRepBodies.count, 'non_manifold_edge_count': non_manifold_count,
    'front_panel_large_planar_face_count': len(front_faces),
    'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]},
    'feature_error_count': len(feature_errors), 'feature_errors': feature_errors,
    'missing_parameter_count': len(missing), 'missing_parameters': missing,
    'extrude_feature_count': root.features.extrudeFeatures.count,
    'fillet_feature_count': root.features.filletFeatures.count,
    'shell_feature_count': root.features.shellFeatures.count,
}
print(result)
if (not doc.isSaved or root.bRepBodies.count != 1 or non_manifold_count
        or len(front_faces) != 1 or feature_errors or missing):
    raise RuntimeError('最终综合自检未通过')
