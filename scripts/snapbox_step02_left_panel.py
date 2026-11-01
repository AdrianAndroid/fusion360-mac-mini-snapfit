# 五件式弹卡收纳盒 - 步骤2 左侧板
# 外壁 X∈[0,2.2]，Y∈[0,180]，Z∈[10.2,160]；底榫(直榫定位)Z4.2..10.2；拎榫把手；前后缘弹性卡钩
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
BoxL, BoxW, BoxH = 260.0, 180.0, 160.0
WallT, FloorT = 2.2, 2.2
RimH, TenonD, TenonW, Gap = 8.0, 6.0, 12.0, 0.2
base = next(b for b in root.bRepBodies if b.name == '01_底座总成')

def world_to_sketch(sketch, point):
    inv = sketch.transform.copy()
    if not inv.invert(): raise RuntimeError('逆变换失败')
    point.transformBy(inv); return point

def world_rect_yz(sk, y1, z1, y2, z2):
    pts = [(y1, z1), (y2, z1), (y2, z2), (y1, z2)]
    loc = [world_to_sketch(sk, adsk.core.Point3D.create(0, y/10, z/10)) for y, z in pts]
    for i in range(4):
        sk.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

def world_rect_xy(sk, z, x1, y1, x2, y2):
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    loc = [world_to_sketch(sk, adsk.core.Point3D.create(x/10, y/10, z/10)) for x, y in pts]
    for i in range(4):
        sk.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

def world_circle_yz(sk, cy, cz, r):
    p = world_to_sketch(sk, adsk.core.Point3D.create(0, cy/10, cz/10))
    sk.sketchCurves.sketchCircles.addByCenterRadius(p, r/10)

def profiles_of(sk):
    c = adsk.core.ObjectCollection.create()
    for p in sk.profiles: c.add(p)
    return c

def one_side(name, sketch, axis, positive, distance, op, target=None):
    fi = root.features.extrudeFeatures.createInput(profiles_of(sketch), op)
    if target is not None:
        tg = adsk.core.ObjectCollection.create(); tg.add(target); fi.targetBodies = tg
    _, _, _, normal = sketch.transform.getAsCoordinateSystem()
    comp = getattr(normal, axis)
    is_pos = comp > 0 if positive else comp < 0
    fi.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')),
        adsk.fusion.ExtentDirections.PositiveExtentDirection if is_pos else adsk.fusion.ExtentDirections.NegativeExtentDirection,
        adsk.core.ValueInput.createByString('0 deg'))
    f = root.features.extrudeFeatures.add(fi); f.name = name; return f

def through_cut(name, sketch, target, distance=16.0):
    fi = root.features.extrudeFeatures.createInput(profiles_of(sketch), adsk.fusion.FeatureOperations.CutFeatureOperation)
    tg = adsk.core.ObjectCollection.create(); tg.add(target); fi.targetBodies = tg
    fi.setTwoSidesExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')),
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')))
    f = root.features.extrudeFeatures.add(fi); f.name = name; return f

def offset_yz(x, name):
    pi = root.constructionPlanes.createInput()
    pi.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByString(f'{x} mm'))
    pl = root.constructionPlanes.add(pi); pl.name = name; return pl

def offset_xy(z, name):
    pi = root.constructionPlanes.createInput()
    pi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByString(f'{z} mm'))
    pl = root.constructionPlanes.add(pi); pl.name = name; return pl

# --- 主体+底榫：YZ草图(X=0)，拉伸+X 2.2 ---
sk = root.sketches.add(root.yZConstructionPlane); sk.name = '02_左侧板主体草图'
# 板身 Y0..180, Z10.2..160
world_rect_yz(sk, 0, FloorT+RimH, BoxW, BoxH)
# 底榫 3个（直榫定位）Z4.2..10.2
for cy in [30.0, 90.0, 150.0]:
    world_rect_yz(sk, cy-TenonW/2, FloorT+RimH-TenonD, cy+TenonW/2, FloorT+RimH)
one_side('02_左侧板主体+底榫', sk, 'x', True, WallT,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
left = next(b for b in root.bRepBodies if b.name != '01_底座总成')
left.name = '02_左侧板'

# --- 弹性卡钩：前后缘各2个，向外凸5mm，重叠1mm融入板身 ---
sk = root.sketches.add(root.yZConstructionPlane); sk.name = '02_左侧板卡钩草图'
for cz in [48.0, 118.0]:
    world_rect_yz(sk, -6.0, cz, 1.0, cz+4.0)      # 前缘钩 Y -6..1(重叠)
    world_rect_yz(sk, BoxW-1.0, cz, BoxW+6.0, cz+4.0)  # 后缘钩 Y 179..186(重叠)
one_side('02_左侧板弹性卡钩_4个', sk, 'x', True, WallT,
         adsk.fusion.FeatureOperations.JoinFeatureOperation, left)

# --- 拎榫：外凸把手法兰+贯通孔（法兰高20mm，孔完全包在内避免相切） ---
sk = root.sketches.add(offset_xy(136.0, '02_拎榫法兰底_Z136')); sk.name = '02_拎榫法兰草图'
world_rect_xy(sk, 136.0, -12.0, 58.0, 1.0, 122.0)   # X -12..1(重叠), Y58..122
one_side('02_拎榫法兰_Z136..156', sk, 'z', True, 20.0,
         adsk.fusion.FeatureOperations.JoinFeatureOperation, left)
sk = root.sketches.add(offset_yz(1.1, '02_拎榫孔平面_X1.1')); sk.name = '02_拎榫孔草图'
world_circle_yz(sk, 90.0, 145.0, 7.0)
through_cut('02_拎榫贯通孔_r7', sk, left, 16.0)

non_manifold = sum(1 for e in left.edges if e.faces.count > 2)
box = left.boundingBox
print({'step': 2, 'design': app.activeDocument.name,
       'bodies': [b.name for b in root.bRepBodies],
       'left_bodies': left.name,
       'non_manifold': non_manifold,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
