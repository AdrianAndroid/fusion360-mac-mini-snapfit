app = adsk.core.Application.get()
vp = app.activeViewport
root = app.activeProduct.rootComponent
# 取全部实体包围盒中心
bodies = [b for b in root.bRepBodies]
mins = [float('inf')]*3; maxs = [float('-inf')]*3
for b in bodies:
    bb = b.boundingBox
    for j,c in enumerate(('x','y','z')):
        mins[j]=min(mins[j],getattr(bb.minPoint,c)); maxs[j]=max(maxs[j],getattr(bb.maxPoint,c))
cx=(mins[0]+maxs[0])/2; cy=(mins[1]+maxs[1])/2; cz=(mins[2]+maxs[2])/2
cam = vp.camera
cam.isSmoothTransition = False
cam.cameraType = adsk.core.CameraTypes.PerspectiveCameraType
# 从上方偏前上方俯视，清晰显示顶部开口空腔
cam.eye = adsk.core.Point3D.create(cx-1.0, cy+1.4, cz+3.4)
cam.target = adsk.core.Point3D.create(cx, cy, cz*0.9)
cam.upVector = adsk.core.Vector3D.create(0.0, 1.0, 0.0)
vp.camera = cam
vp.fit()
import os, tempfile
path = '/Users/zhaojian/code/fusion360/local_checkpoints/20261101_snapbox_5part/opening_top_iso.png'
ok = vp.saveAsImageFile(path, 1200, 1000)
print({'saved': ok, 'path': path, 'center_mm': [round(cx*10,1),round(cy*10,1),round(cz*10,1)]})
