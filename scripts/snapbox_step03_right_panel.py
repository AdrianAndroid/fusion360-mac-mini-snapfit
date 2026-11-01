# 五件式弹卡收纳盒 - 步骤3 右侧板（左侧镜像，X∈[257.8,260]）
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
BoxL, BoxW, BoxH = 300.0, 210.0, 210.0
WallT, FloorT = 2.2, 2.2
RimH, TenonD, TenonW, Gap = 8.0, 6.0, 12.0, 0.2
XP0 = BoxL - WallT   # 257.8

def world_to_sketch(sketch, point):
    inv = sketch.transform.copy()
    if not inv.invert(): raise RuntimeError('逆变换失败')
    point.transformBy(inv); return point

def world_rect_yz(sk, px, y1, z1, y2, z2):
    pts = [(y1, z1), (y2, z1), (y2, z2), (y1, z2)]
    loc = [world_to_sketch(sk, adsk.core.Point3D.create(px/10, y/10, z/10)) for y, z in pts]
    for i in range(4):
        sk.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

def world_rect_xy(sk, z, x1, y1, x2, y2):
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    loc = [world_to_sketch(sk, adsk.core.Point3D.create(x/10, y/10, z/10)) for x, y in pts]
    for i in range(4):
        sk.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

def world_circle_yz(sk, px, cy, cz, r):
    p = world_to_sketch(sk, adsk.core.Point3D.create(px/10, cy/10, cz/10))
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

# --- 主体+底榫：YZ草图(X=257.8)，拉伸+X 2.2 ---
sk = root.sketches.add(offset_yz(XP0, '03_右侧板主体平面_X257.8')); sk.name = '03_右侧板主体草图'
world_rect_yz(sk, XP0, 0, FloorT+RimH, BoxW, BoxH)
for cy in [40.0, 105.0, 170.0]:
    world_rect_yz(sk, XP0, cy-TenonW/2, FloorT+RimH-TenonD, cy+TenonW/2, FloorT+RimH)
one_side('03_右侧板主体+底榫', sk, 'x', True, WallT,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
right = next(b for b in root.bRepBodies if b.name not in ('01_底座总成', '02_左侧板'))
right.name = '03_右侧板'

# --- 弹性卡钩：前后缘各2个，向外凸5mm，重叠1mm ---
hook_z = [70.0, 160.0]
sk = root.sketches.add(offset_yz(XP0, '03_右侧板卡钩平面_X297.8')); sk.name = '03_右侧板卡钩草图'
for cz in hook_z:
    world_rect_yz(sk, XP0, -6.0, cz, 1.0, cz+4.0)      # 前缘钩
    world_rect_yz(sk, XP0, BoxW-1.0, cz, BoxW+6.0, cz+4.0)  # 后缘钩
one_side('03_右侧板弹性卡钩_4个', sk, 'x', True, WallT,
         adsk.fusion.FeatureOperations.JoinFeatureOperation, right)

# --- 拎榫：外凸把手法兰(X299..312)+贯通孔 ---
fl_z0 = BoxH - 24.0      # 186
fl_y0 = BoxW/2 - 32.0    # 73
fl_y1 = BoxW/2 + 32.0    # 137
sk = root.sketches.add(offset_xy(fl_z0, '03_拎榫法兰底')); sk.name = '03_拎榫法兰草图'
world_rect_xy(sk, fl_z0, BoxL-1.0, fl_y0, BoxL+12.0, fl_y1)   # X 299..312(重叠到300), Y73..137
one_side('03_拎榫法兰', sk, 'z', True, 20.0,
         adsk.fusion.FeatureOperations.JoinFeatureOperation, right)
sk = root.sketches.add(offset_yz(XP0+WallT/2, '03_拎榫孔平面_X298.9')); sk.name = '03_拎榫孔草图'
world_circle_yz(sk, XP0+WallT/2, BoxW/2, fl_z0+10.0, 7.0)
through_cut('03_拎榫贯通孔_r7', sk, right, 16.0)

non_manifold = sum(1 for e in right.edges if e.faces.count > 2)
box = right.boundingBox
print({'step': 3, 'design': app.activeDocument.name,
       'bodies': [b.name for b in root.bRepBodies],
       'right_bodies': right.name,
       'non_manifold': non_manifold,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
