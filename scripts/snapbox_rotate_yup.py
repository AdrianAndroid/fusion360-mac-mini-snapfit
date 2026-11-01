import adsk.core, adsk.fusion, math
app = adsk.core.Application.get()
root = adsk.fusion.Design.cast(app.activeProduct).rootComponent
mtx = adsk.core.Matrix3D.create()
axis = adsk.core.Vector3D.create(1,0,0)
mtx.setToRotation(math.radians(-90.0), axis, adsk.core.Point3D.create(0,0,0))
oc = adsk.core.ObjectCollection.create()
for b in root.bRepBodies: oc.add(b)
moveFeats = root.features.moveFeatures
moveFeats.add(moveFeats.createInput(oc, mtx))
app.activeViewport.refresh()
out=[]
for b in root.bRepBodies:
    bb=b.boundingBox
    nm=sum(1 for e in b.edges if e.faces.count>2)
    out.append({'name':b.name,'bbox_mm':[round(bb.minPoint.x*10,1),round(bb.minPoint.y*10,1),round(bb.minPoint.z*10,1),round(bb.maxPoint.x*10,1),round(bb.maxPoint.y*10,1),round(bb.maxPoint.z*10,1)],'non_manifold':nm})
print({'moved':root.bRepBodies.count,'bodies':out})
