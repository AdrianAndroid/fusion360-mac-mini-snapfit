app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
report = {'design': app.activeDocument.name, 'bodies': []}
for b in root.bRepBodies:
    nm = sum(1 for e in b.edges if e.faces.count > 2)
    bb = b.boundingBox
    report['bodies'].append({
        'name': b.name,
        'non_manifold': nm,
        'volume_mm3': round(b.volume*1000, 1),
        'bbox_mm': {'min': [round(bb.minPoint.x*10,1), round(bb.minPoint.y*10,1), round(bb.minPoint.z*10,1)],
                    'max': [round(bb.maxPoint.x*10,1), round(bb.maxPoint.y*10,1), round(bb.maxPoint.z*10,1)]}})
report['total_bodies'] = len(root.bRepBodies)
report['total_mass_g'] = round(sum(b.volume for b in root.bRepBodies)*2.7, 1)  # 按PLA密度2.7? 改用Fusion质
print(report)
