app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
if root.bRepBodies.count or root.sketches.count or root.occurrences.count:
    raise RuntimeError('新版初始化失败：当前设计并非空文档')
design.designType = adsk.fusion.DesignTypes.ParametricDesignType
for parameter in list(design.userParameters):
    parameter.deleteMe()
if design.unitsManager.defaultLengthUnits != 'mm':
    raise RuntimeError('文档默认单位不是mm')
print({'initialized': True, 'body_count': root.bRepBodies.count,
       'timeline_count': design.timeline.count, 'units': design.unitsManager.defaultLengthUnits})
