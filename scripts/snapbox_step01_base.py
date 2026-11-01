# 五件式弹卡收纳盒 - 步骤1 底座总成（修正：按平面世界Z画轮廓）
# 单位 mm；原点=底座外左下前角；X长260 Y深180 Z高160；顶面开口Z=160
design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
root = design.rootComponent
BoxL, BoxW, BoxH = 300.0, 210.0, 210.0
WallT, FloorT = 2.2, 2.2
RimH, TenonD, TenonW, Gap = 8.0, 6.0, 12.0, 0.2
if root.bRepBodies.count != 0:
    raise RuntimeError('步骤1要求全新空设计')

def world_to_sketch(sketch, point):
    inv = sketch.transform.copy()
    if not inv.invert():
        raise RuntimeError('逆变换失败')
    point.transformBy(inv)
    return point

def world_rect_xy(sketch, z, x1, y1, x2, y2):
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    loc = [world_to_sketch(sketch, adsk.core.Point3D.create(x/10, y/10, z/10)) for x, y in pts]
    for i in range(4):
        sketch.sketchCurves.sketchLines.addByTwoPoints(loc[i], loc[(i+1) % 4])

def profiles_of(sketch):
    c = adsk.core.ObjectCollection.create()
    for p in sketch.profiles:
        c.add(p)
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

def offset_xy(offset, name):
    pi = root.constructionPlanes.createInput()
    pi.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByString(f'{offset} mm'))
    pl = root.constructionPlanes.add(pi); pl.name = name; return pl

# --- 1) 底板 260x180x2.2 @ Z 0..2.2 ---
sk = root.sketches.add(root.xYConstructionPlane); sk.name = '01_底板草图'
world_rect_xy(sk, 0, 0, 0, BoxL, BoxW)
one_side('01_底板_260x180x2.2', sk, 'z', True, FloorT,
         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
base = next(b for b in root.bRepBodies)
base.name = '01_底座总成'

# --- 2) 四周承榫沿 RimH=8 @ Z 2.2..10.2 ---
rim_plane = offset_xy(FloorT, '01_承榫沿底平面_Z2.2')
sk = root.sketches.add(rim_plane); sk.name = '01_四周承榫沿草图'
world_rect_xy(sk, FloorT, 0, 0, WallT, BoxW)                 # 左沿
world_rect_xy(sk, FloorT, BoxL-WallT, 0, BoxL, BoxW)         # 右沿
world_rect_xy(sk, FloorT, WallT, 0, BoxL-WallT, WallT)       # 前沿
world_rect_xy(sk, FloorT, WallT, BoxW-WallT, BoxL-WallT, BoxW)  # 后沿
one_side('01_四周承榫沿_高8mm', sk, 'z', True, RimH,
         adsk.fusion.FeatureOperations.JoinFeatureOperation, base)
if root.bRepBodies.count != 1:
    raise RuntimeError('承榫沿未并入底座')

# --- 3) 底部支撑脚 4个 @ Z -5..0 ---
foot_plane = offset_xy(-5.0, '01_脚底平面_Z-5')
sk = root.sketches.add(foot_plane); sk.name = '01_支撑脚草图'
for (fx1, fy1, fx2, fy2) in [(4, 6, 40, 24), (4, BoxW-24, 40, BoxW-6),
                              (BoxL-40, 6, BoxL-4, 24), (BoxL-40, BoxW-24, BoxL-4, BoxW-6)]:
    world_rect_xy(sk, -5.0, fx1, fy1, fx2, fy2)
one_side('01_支撑脚_高5mm', sk, 'z', True, 5.0,
         adsk.fusion.FeatureOperations.JoinFeatureOperation, base)

# --- 4) 承榫沿榫槽（从沿底面Z=2.2向上整段切除8mm），单边间隙0.2 ---
slot_w = TenonW + 2*Gap  # 12.4
tenon_y = [40.0, 105.0, 170.0]   # Y向底榫位(左右缘槽)，按210宽均匀
tenon_x = [60.0, 150.0, 240.0]   # X向底榫位(前后缘槽)，按300长均匀
sk = root.sketches.add(offset_xy(FloorT, '01_承榫沿底面_Z2.2_榫槽')); sk.name = '01_承榫沿榫槽草图'
for cy in tenon_y:
    world_rect_xy(sk, FloorT, 0, cy-slot_w/2, WallT, cy+slot_w/2)                    # 左沿
    world_rect_xy(sk, FloorT, BoxL-WallT, cy-slot_w/2, BoxL, cy+slot_w/2)            # 右沿
for cx in tenon_x:
    world_rect_xy(sk, FloorT, cx-slot_w/2, 0, cx+slot_w/2, WallT)                    # 前沿
    world_rect_xy(sk, FloorT, cx-slot_w/2, BoxW-WallT, cx+slot_w/2, BoxW)            # 后沿
one_side('01_承榫沿榫槽_12个_深8mm', sk, 'z', True, RimH,
         adsk.fusion.FeatureOperations.CutFeatureOperation, base)

non_manifold = sum(1 for e in base.edges if e.faces.count > 2)
box = base.boundingBox
print({'step': 1, 'design': app.activeDocument.name,
       'bodies': [b.name for b in root.bRepBodies],
       'body_count': root.bRepBodies.count,
       'non_manifold': non_manifold,
       'mortise_slots': 12,
       'bbox_mm': {'min': [box.minPoint.x*10, box.minPoint.y*10, box.minPoint.z*10],
                   'max': [box.maxPoint.x*10, box.maxPoint.y*10, box.maxPoint.z*10]}})
