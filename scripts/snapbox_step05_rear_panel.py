# 五件式弹卡收纳盒 - 步骤5 后盖板（实心普通板）
# 后壁 Y∈[177.8,180]，X∈[2.2,257.8]，Z∈[10.2,160]；3底榫(直榫)；插入卡紧；固定卡槽；不设格栅/出线槽(参考图非镂空)
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
# 若已存在旧版后盖板则删除（幂等重跑）
for b in [b for b in root.bRepBodies if b.name == '05_后盖板']:
    b.deleteMe()
BoxL, BoxW, BoxH = 300.0, 210.0, 210.0
WallT, FloorT = 2.2, 2.2
RimH, TenonD, TenonW, Gap = 8.0, 6.0, 12.0, 0.2
YP0 = BoxW - WallT   # 177.8

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

# --- 主体+底榫+插入卡紧：XZ草图(Y=207.8)，拉伸+Y 2.2 ---
sk = root.sketches.add(offset_xz(YP0, '05_后盖板主体平面_Y207.8')); sk.name = '05_后盖板主体草图'
world_rect_xz(sk, YP0, WallT, FloorT+RimH, BoxL-WallT, BoxH)   # 板身 X2.2..297.8 Z10.2..210
for cx in [60.0, 150.0, 240.0]:
    world_rect_xz(sk, YP0, cx-TenonW/2, FloorT+RimH-TenonD, cx+TenonW/2, FloorT+RimH)
world_rect_xz(sk, YP0, BoxL/2-12.0, 8.2, BoxL/2+12.0, 10.5)    # 插入卡紧 下凸 X138..162(重叠0.3)
one_side('05_后盖板主体+底榫+插入卡紧', sk, 'y', True, WallT,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
rear = next(b for b in root.bRepBodies if b.name not in ('01_底座总成', '02_左侧板', '03_右侧板', '04_前盖板'))
rear.name = '05_后盖板'

# --- 固定卡槽：左右缘各2个贯穿Y的槽 ---
sk = root.sketches.add(offset_xz(YP0+WallT/2, '05_固定卡槽平面_Y208.9')); sk.name = '05_后盖板固定卡槽草图'
for cz in [70.0, 160.0]:
    world_rect_xz(sk, YP0+WallT/2, 8.0, cz, 14.0, cz+4.0)
    world_rect_xz(sk, YP0+WallT/2, BoxL-14.0, cz, BoxL-8.0, cz+4.0)
through_cut('05_固定卡槽_4个', sk, rear, 2.5)

# 注：后盖板为实心普通板（参考图非镂空），仅保留底榫/插入卡紧/固定卡槽，不设格栅与出线槽

non_manifold = sum(1 for e in rear.edges if e.faces.count > 2)
box = rear.boundingBox
print({'step': 5, 'design': app.activeDocument.name,
       'bodies': [b.name for b in root.bRepBodies],
       'rear_bodies': rear.name,
       'non_manifold': non_manifold,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
