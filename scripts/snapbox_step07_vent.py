# 五件式弹卡收纳盒 - 步骤7 四块立板加散热通风槽（竖向格栅，避开连接结构）
# 前后盖板各5条竖槽(X中心区,Z中上部)；左右侧板各3条竖槽(Y中心区,Z中上部)；全部贯穿板厚
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
BoxL, BoxW, BoxH = 300.0, 210.0, 210.0
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

def world_rect_yz(sk, px, y1, z1, y2, z2):
    pts = [(y1, z1), (y2, z1), (y2, z2), (y1, z2)]
    loc = [world_to_sketch(sk, adsk.core.Point3D.create(px/10, y/10, z/10)) for y, z in pts]
    for i in range(4):
        sk.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

def profiles_of(sk):
    c = adsk.core.ObjectCollection.create()
    for p in sk.profiles: c.add(p)
    return c

def through_cut(name, sketch, target, distance):
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

def offset_yz(x, name):
    pi = root.constructionPlanes.createInput()
    pi.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByString(f'{x} mm'))
    pl = root.constructionPlanes.add(pi); pl.name = name; return pl

bodies = {b.name: b for b in root.bRepBodies}

# --- 前盖板 04 与 后盖板 05：中央5条竖向格栅 Z60..185 ---
for name, ymid, yn in [('04_前盖板', WallT/2, 'Y1.1'), ('05_后盖板', BoxW-WallT/2, 'Y208.9')]:
    sk = root.sketches.add(offset_xz(ymid, f'07_{name}格栅平面_{yn}')); sk.name = f'07_{name}格栅草图'
    for gx in [70.0, 110.0, 150.0, 190.0, 230.0]:
        world_rect_xz(sk, ymid, gx-4.0, 60.0, gx+4.0, 185.0)   # 宽8, Z60..185,避开底榫/卡槽/卡紧
    through_cut(f'07_{name}散热格栅_5条', sk, bodies[name], 2.5)

# --- 左/右侧板 02/03：中央3条竖向格栅 Z60..180 ---
for name, xmid, xn in [('02_左侧板', WallT/2, 'X1.1'), ('03_右侧板', BoxL-WallT/2, 'X298.9')]:
    sk = root.sketches.add(offset_yz(xmid, f'07_{name}格栅平面_{xn}')); sk.name = f'07_{name}格栅草图'
    for gy in [70.0, 110.0, 150.0]:
        world_rect_yz(sk, xmid, gy-4.0, 60.0, gy+4.0, 180.0)   # 宽8, Z60..180,避开卡钩/拎榫/底榫
    through_cut(f'07_{name}散热格栅_3条', sk, bodies[name], 3.0)

report = []
for name in ['01_底座总成', '02_左侧板', '03_右侧板', '04_前盖板', '05_后盖板']:
    b = bodies[name]
    report.append({'name': name, 'non_manifold': sum(1 for e in b.edges if e.faces.count > 2),
                   'vol_mm3': round(b.volume*1000, 1)})
print({'design': app.activeDocument.name, 'bodies': report})
