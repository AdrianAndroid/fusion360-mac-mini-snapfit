# 五件式弹卡收纳盒 - 步骤8 内部左右分隔板（半高）
# Mac mini 200x110 靠左侧壁区；隔板 X∈[114,116.2] 厚2.2，Y∈[2.2,207.8] 顶满内宽，Z∈[10.2,110.2] 半高约100
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
BoxL, BoxW, BoxH = 300.0, 210.0, 210.0
WallT, FloorT = 2.2, 2.2
RimH = 8.0
XP0 = BoxL - WallT

def world_to_sketch(sketch, point):
    inv = sketch.transform.copy()
    if not inv.invert(): raise RuntimeError('逆变换失败')
    point.transformBy(inv); return point

def world_rect_yz(sk, px, y1, z1, y2, z2):
    pts = [(y1, z1), (y2, z1), (y2, z2), (y1, z2)]
    loc = [world_to_sketch(sk, adsk.core.Point3D.create(px/10, y/10, z/10)) for y, z in pts]
    for i in range(4):
        sk.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

def profiles_of(sk):
    c = adsk.core.ObjectCollection.create()
    for p in sk.profiles: c.add(p)
    return c

def one_side(name, sketch, axis, positive, distance, op):
    fi = root.features.extrudeFeatures.createInput(profiles_of(sketch), op)
    _, _, _, normal = sketch.transform.getAsCoordinateSystem()
    comp = getattr(normal, axis)
    is_pos = comp > 0 if positive else comp < 0
    fi.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f'{distance} mm')),
        adsk.fusion.ExtentDirections.PositiveExtentDirection if is_pos else adsk.fusion.ExtentDirections.NegativeExtentDirection,
        adsk.core.ValueInput.createByString('0 deg'))
    f = root.features.extrudeFeatures.add(fi); f.name = name; return f

def offset_yz(x, name):
    pi = root.constructionPlanes.createInput()
    pi.setByOffset(root.yZConstructionPlane, adsk.core.ValueInput.createByString(f'{x} mm'))
    pl = root.constructionPlanes.add(pi); pl.name = name; return pl

# --- 左右分隔板：YZ草图(X=115.1)，向两侧拉伸±1.1 → X[114,116.2] ---
Xmid = 115.1
Y0, Y1 = 2.2, BoxW-2.2      # Y2.2..207.8 顶满内宽
Z0, Z1 = FloorT+RimH, FloorT+RimH+100.0   # Z10.2..110.2 半高100
sk = root.sketches.add(offset_yz(Xmid, '08_隔板平面_X115.1')); sk.name = '08_左右分隔板草图'
world_rect_yz(sk, Xmid, Y0, Z0, Y1, Z1)
one_side('08_左右分隔板_半高100', sk, 'x', True, WallT,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
part = next(b for b in root.bRepBodies if b.name not in ('01_底座总成', '02_左侧板', '03_右侧板', '04_前盖板', '05_后盖板'))
part.name = '07_左右分隔板'

non_manifold = sum(1 for e in part.edges if e.faces.count > 2)
box = part.boundingBox
print({'step': 8, 'design': app.activeDocument.name,
       'bodies': [b.name for b in root.bRepBodies],
       'divider': part.name,
       'non_manifold': non_manifold,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
