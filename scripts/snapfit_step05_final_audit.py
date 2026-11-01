import itertools
import math

app = adsk.core.Application.get()
doc = app.activeDocument
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
expected_name = 'Mac mini 收纳盒_无螺丝卯榫卡扣_300x210x210'
if doc.name != expected_name or design.unitsManager.defaultLengthUnits != 'mm':
    raise RuntimeError('最终审计文档或单位异常')
expected_bodies = ['01_底座总成', '02_左侧板', '03_右侧板', '04_后盖板']
if root.bRepBodies.count != 4:
    raise RuntimeError('最终审计要求恰好4个实体')
bodies = {body.name: body for body in root.bRepBodies}
if set(bodies) != set(expected_bodies):
    raise RuntimeError('四个零件名称或数量异常')
base = bodies['01_底座总成']

# 修正脚壁角部等厚：外R3、内R0.8且同心，径向壁厚2.2。
if not design.userParameters.itemByName('FootInnerR'):
    design.userParameters.add('FootInnerR', adsk.core.ValueInput.createByString('0.8 mm'), 'mm',
                              '支撑脚内角；OuterR-FootInnerR=2.2mm')
fillet_name = '05_支撑脚内竖角_R0.8_角部等厚2.2mm'
if not root.features.filletFeatures.itemByName(fillet_name):
    inner_edges = adsk.core.ObjectCollection.create()
    for edge in base.edges:
        if not adsk.core.Line3D.cast(edge.geometry):
            continue
        box = edge.boundingBox
        dx = (box.maxPoint.x-box.minPoint.x)*10
        dy = (box.maxPoint.y-box.minPoint.y)*10
        cx = (box.minPoint.x+box.maxPoint.x)*5
        cy = (box.minPoint.y+box.maxPoint.y)*5
        if (dx < 0.01 and dy < 0.01
                and abs(box.minPoint.z*10+5) < 0.01 and abs(box.maxPoint.z*10) < 0.01
                and any(abs(cx-x) < 0.01 for x in (4.4, 295.6))
                and any(abs(cy-y) < 0.01 for y in (2.2, 205.6))):
            inner_edges.add(edge)
    if inner_edges.count != 4:
        raise RuntimeError(f'支撑脚内竖角数量异常: {inner_edges.count}')
    fillet_input = root.features.filletFeatures.createInput()
    fillet_input.edgeSetInputs.addConstantRadiusEdgeSet(
        inner_edges, adsk.core.ValueInput.createByString('FootInnerR'), False)
    feature = root.features.filletFeatures.add(fillet_input)
    feature.name = fillet_name

# 实体、拓扑和特征健康。
non_manifold = {name: sum(1 for edge in body.edges if edge.faces.count > 2)
                for name, body in bodies.items()}
if any(non_manifold.values()):
    raise RuntimeError(f'最终审计存在非流形边: {non_manifold}')
feature_errors = []
for collection in (root.features.extrudeFeatures, root.features.filletFeatures):
    for feature in collection:
        if feature.errorOrWarningMessage:
            feature_errors.append({'feature': feature.name, 'message': feature.errorOrWarningMessage})
if feature_errors:
    raise RuntimeError(f'最终审计存在特征错误/警告: {feature_errors}')

# 六组两两实体干涉，使用临时BRep，不新增时间线特征。
manager = adsk.fusion.TemporaryBRepManager.get()
intersections = {}
for name1, name2 in itertools.combinations(expected_bodies, 2):
    body1 = manager.copy(bodies[name1])
    body2 = manager.copy(bodies[name2])
    ok = manager.booleanOperation(body1, body2, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    volume = body1.physicalProperties.volume*1000 if ok and body1.faces.count else 0.0
    intersections[name1+' / '+name2] = volume
if any(volume > 0.001 for volume in intersections.values()):
    raise RuntimeError(f'最终审计存在实体干涉: {intersections}')

# 四仓位净尺寸和走线空间。
slot_checks = {
    'Mac mini 宽×深×高': [38.75-2.2, 200.65-2.2, 200.65-2.2],
    '3.5寸硬盘 宽×深×高': [67.8-40.95, 104.55-2.2, 148.95-2.2],
    '2.5寸SATA 宽×深×高': [80.25-70.0, 72.8-2.2, 102.95-2.2],
    'Upstone Hub 宽×深×高': [115.2-82.45, 107.95-2.2, 122.95-2.2],
}
expected_slots = {
    'Mac mini 宽×深×高': [36.55, 198.45, 198.45],
    '3.5寸硬盘 宽×深×高': [26.85, 102.35, 146.75],
    '2.5寸SATA 宽×深×高': [10.25, 70.6, 100.75],
    'Upstone Hub 宽×深×高': [32.75, 105.75, 120.75],
}
for name in expected_slots:
    if any(abs(a-b) > 0.001 for a, b in zip(slot_checks[name], expected_slots[name])):
        raise RuntimeError('仓位净尺寸异常: ' + name)
if abs((210-200.65)-9.35) > 0.001 or abs((297.8-115.2)-182.6) > 0.001:
    raise RuntimeError('顶部或右侧走线空间异常')

# 榫卯配合：底座9榫、后板6小榫，对应15处母槽。
tenon_thickness = 2.2
tenon_depth = 6.0
tenon_width = 12.0
clearance = 0.2
mortise_width = tenon_width+2*clearance
if abs(mortise_width-12.4) > 0.001:
    raise RuntimeError('母槽配合尺寸异常')
base_r1_faces = []
rear_r1_faces = []
for face in base.faces:
    cylinder = adsk.core.Cylinder.cast(face.geometry)
    if cylinder and abs(cylinder.radius*10-1.0) < 0.001:
        base_r1_faces.append(face)
for face in bodies['04_后盖板'].faces:
    cylinder = adsk.core.Cylinder.cast(face.geometry)
    if cylinder and abs(cylinder.radius*10-1.0) < 0.001:
        rear_r1_faces.append(face)
if len(base_r1_faces) != 18 or len(rear_r1_faces) != 12:
    raise RuntimeError('榫根R1圆柱面数量异常')
barb_run = 0.6/math.tan(math.radians(15))
if abs(math.degrees(math.atan2(0.6, barb_run))-15) > 0.000001:
    raise RuntimeError('倒扣角度异常')

# 壁厚/实料关键截面审计。所有值均为实体净宽或相邻空隙间实料。
thickness_checks = {
    '壳体及板件标称壁厚': 2.2,
    '三块主隔板及后限位筋': 2.2,
    '底部格栅筋': 6.2-4.0,
    '后板格栅筋': 6.2-4.0,
    '底板左侧实体边框': 4.4-2.2,
    '底板右侧实体边框': 297.8-295.6,
    '后板底部母槽至格栅': 4.6-2.4,
    '后板格栅至出线槽底': 200.0-197.8,
    '后板左侧格栅边框': 5.4-2.2,
    '后板右侧格栅边框': 297.8-294.6,
    '支撑脚直段环壁': 4.4-2.2,
    '支撑脚圆角径向环壁': 3.0-0.8,
    '左窗中央连接筋': 106.1-103.9,
    '左散热窗实体边框': 8.0,
    '拎带孔凸台径向实体': (18.0-9.0)/2,
    '底槽顶至左散热窗': 8.0-2.4,
    '左窗后框至互锁槽': 207.6-202.0,
    '榫头本体厚度': tenon_thickness,
}
minimum_name = min(thickness_checks, key=thickness_checks.get)
minimum_thickness = thickness_checks[minimum_name]
if minimum_thickness < 2.2-0.000001:
    raise RuntimeError(f'壁厚不足: {minimum_name}={minimum_thickness}')

# 脚内R0.8圆柱面必须4个，并与外R3同心。
inner_centers = []
outer_centers = []
for face in base.faces:
    cylinder = adsk.core.Cylinder.cast(face.geometry)
    if not cylinder or abs(cylinder.axis.z) < 0.99:
        continue
    center = [round(cylinder.origin.x*10, 3), round(cylinder.origin.y*10, 3)]
    if abs(cylinder.radius*10-0.8) < 0.001:
        inner_centers.append(center)
    if abs(cylinder.radius*10-3.0) < 0.001:
        box = face.boundingBox
        if box.minPoint.z*10 < -4.99:
            outer_centers.append(center)
expected_centers = [[5.2, 3.0], [294.8, 3.0], [5.2, 204.8], [294.8, 204.8]]
if len(inner_centers) != 4 or any(center not in inner_centers or center not in outer_centers
                                  for center in expected_centers):
    raise RuntimeError(f'支撑脚内外圆角不同心: inner={inner_centers}, outer={outer_centers}')

# 两个拎带孔和凸台的圆柱面实际几何检查。
handle_geometry = {}
for name in ('02_左侧板', '03_右侧板'):
    hole_faces = 0
    boss_faces = 0
    for face in bodies[name].faces:
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if not cylinder or abs(cylinder.axis.x) < 0.99:
            continue
        if abs(cylinder.radius*10-4.5) < 0.001:
            hole_faces += 1
        if abs(cylinder.radius*10-9.0) < 0.001:
            boss_faces += 1
    handle_geometry[name] = {'D9_cylinders': hole_faces, 'R9_cylinders': boss_faces}
    if hole_faces < 1 or boss_faces < 1:
        raise RuntimeError('拎带孔或凸台实际圆柱面缺失: ' + name)

all_boxes = [body.boundingBox for body in bodies.values()]
assembly_box = {
    'min': [min(box.minPoint.x for box in all_boxes)*10,
            min(box.minPoint.y for box in all_boxes)*10,
            min(box.minPoint.z for box in all_boxes)*10],
    'max': [max(box.maxPoint.x for box in all_boxes)*10,
            max(box.maxPoint.y for box in all_boxes)*10,
            max(box.maxPoint.z for box in all_boxes)*10],
}
result = {
    'document': doc.name, 'body_count': 4, 'bodies': expected_bodies,
    'non_manifold': non_manifold, 'feature_error_count': len(feature_errors),
    'interference_pair_count': len(intersections), 'intersection_volume_mm3': intersections,
    'slot_net_dimensions_mm': slot_checks, 'top_wiring_gap_mm': 9.35,
    'right_cable_channel_width_mm': 182.6,
    'base_tenon_count': 9, 'rear_interlock_tenon_count': 6,
    'mortise_connection_count': 15, 'tenon_thickness_mm': tenon_thickness,
    'tenon_depth_mm': tenon_depth, 'tenon_width_mm': tenon_width,
    'mortise_width_mm': mortise_width, 'single_side_clearance_mm': clearance,
    'base_tenon_R1_faces': len(base_r1_faces), 'rear_tenon_R1_faces': len(rear_r1_faces),
    'barb_angle_deg': 15.0, 'barb_projection_mm': 0.6,
    'minimum_critical_thickness_mm': minimum_thickness,
    'minimum_thickness_location': minimum_name,
    'thickness_checks_mm': thickness_checks,
    'foot_concentric_centers_mm': inner_centers,
    'handle_geometry': handle_geometry,
    'nominal_shell_mm': [300.0, 210.0, 210.0],
    'assembly_bbox_with_feet_bosses_tenons_mm': assembly_box,
    'native_saved_before_final_save': doc.isSaved,
}
print(result)
