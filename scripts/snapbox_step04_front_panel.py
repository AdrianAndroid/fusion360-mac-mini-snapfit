# 五件式弹卡收纳盒 - 步骤4 前盖板
# 前壁 Y∈[0,2.2]，X∈[2.2,257.8]，Z∈[10.2,160]；3底榫(直榫)；推入卡紧；左右缘固定卡槽
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
BoxL, BoxW, BoxH = 260.0, 180.0, 160.0
WallT, FloorT = 2.2, 2.2
RimH, TenonD, TenonW, Gap = 8.0, 6.0, 12.0, 0.2

def world_to_sketch(sketch, point):
    inv = sketch.transform.copy()
    if not inv.invert(): raise RuntimeError('逆变换失败')
    point.transformBy(inv); return point

def world_rect_xz(sk, y, x1, z1, x2, z2):
    pts = [(x1, z1), (x2, z1), (x2, z2), (x1, z2)]
    loc = [world_to_sketch(sk, adsk.core.Point3D.create(x/10, y/10, z/10)) for x, z in pts]
    for i in range(4):
        sk.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

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

def through_cut(name, sketch, target, distance=2.5):
    fi = root.features.extrudeFeatures.createInput(profiles_of(sketch), adsk.fusion.FeatureOperations.CutFeatureOperation)
    tg = adsk.core.ObjectCollection.create(); tg.add(target); fi.targetBodies = tg
    fi.setTwoSidesExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')),
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')))
    f = root.features.extrudeFeatures.add(fi); f.name = name; return f

def offset_xz(y, name):
    pi = root.constructionPlanes.createInput()
    pi.setByOffset(root.xZConstructionPlane, adsk.core.ValueInput.createByString(f'{y} mm'))
    pl = root.constructionPlanes.add(pi); pl.name = name; return pl

# --- 主体+底榫+推入卡紧：XZ草图(Y=0)，拉伸+Y 2.2 ---
sk = root.sketches.add(root.xZConstructionPlane); sk.name = '04_前盖板主体草图'
world_rect_xz(sk, 0, WallT, FloorT+RimH, BoxL-WallT, BoxH)   # 板身 X2.2..257.8 Z10.2..160
for cx in [50.0, 130.0, 210.0]:                               # 底榫(直榫) X±6 Z4.2..10.2
    world_rect_xz(sk, 0, cx-TenonW/2, FloorT+RimH-TenonD, cx+TenonW/2, FloorT+RimH)
world_rect_xz(sk, 0, 118.0, 8.2, 142.0, 10.5)                  # 推入卡紧 下凸(重叠0.3)
one_side('04_前盖板主体+底榫+推入卡紧', sk, 'y', True, WallT,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
front = next(b for b in root.bRepBodies if b.name not in ('01_底座总成', '02_左侧板', '03_右侧板'))
front.name = '04_前盖板'

# --- 固定卡槽：左右缘各2个贯穿Y的槽(承接侧板弹性卡钩) ---
sk = root.sketches.add(offset_xz(WallT/2, '04_固定卡槽平面_Y1.1')); sk.name = '04_前盖板固定卡槽草图'
for cz in [48.0, 118.0]:
    world_rect_xz(sk, WallT/2, 8.0, cz, 14.0, cz+4.0)         # 左缘槽
    world_rect_xz(sk, WallT/2, BoxL-14.0, cz, BoxL-8.0, cz+4.0)  # 右缘槽
through_cut('04_固定卡槽_4个', sk, front, 2.5)

non_manifold = sum(1 for e in front.edges if e.faces.count > 2)
box = front.boundingBox
print({'step': 4, 'design': app.activeDocument.name,
       'bodies': [b.name for b in root.bRepBodies],
       'front_bodies': front.name,
       'non_manifold': non_manifold,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
