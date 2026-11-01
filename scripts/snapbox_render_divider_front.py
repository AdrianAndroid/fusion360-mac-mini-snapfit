# 渲染正面清晰视角：隔板竖直立着、上方空
import adsk.core, adsk.fusion
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
vp = app.activeViewport
root = design.rootComponent
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
# 从盒子前方(+Y)略上方看，隔板竖直立着、顶部空间可见
cam.eye = adsk.core.Point3D.create(cx-1.2, cy+2.6, cz+1.4)
cam.target = adsk.core.Point3D.create(cx, cy*0.92, cz*0.85)
cam.upVector = adsk.core.Vector3D.create(0.0, 0.0, 1.0)
vp.camera = cam
vp.fit()
import time; time.sleep(0.6)
out = '/Users/zhaojian/code/fusion360/local_checkpoints/20261101_snapbox_5part/divider_front.png'
ok = vp.saveAsImageFile(out, 1400, 1100)
print({'saved': ok, 'path': out})
