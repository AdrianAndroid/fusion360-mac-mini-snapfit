# -*- coding: utf-8 -*-
# 生成五件式弹卡收纳盒 三视图尺寸标注图（PIL，精确参数）
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
def F(sz): return ImageFont.truetype(FONT_PATH, sz)

# ---- 精确尺寸(mm) ----
L, W, H = 300.0, 210.0, 210.0          # 长X 宽Z 高Y
T = 2.2                                 # 壁厚/地板厚
rim = 8.0                               # 底脚缘高
# 散热槽
vent_w = 8.0
front_x = [70,110,150,190,230]         # 前后盖板 5条竖槽 X位
front_z0, front_z1 = 60.0, 185.0       # 槽高范围(Y)
side_w = [70,110,150]                  # 左右板 3条竖槽 宽向Z位
side_z0, side_z1 = 60.0, 180.0
# 隔板
div_x1, div_x2 = 115.1, 117.3          # 半高隔板 X
div_y0, div_y1 = 10.2, 110.2
# 底榫
tenon_x = [60,150,240]
tenon_w = [40,105,170]

SCALE = 1.0   # px/mm
pad = 55       # 标注留白
W_IMG, H_IMG = 1560, 1020
img = Image.new("RGB",(W_IMG,H_IMG),(250,250,248))
d = ImageDraw.Draw(img)
f_title=F(30); f_sub=F(18); f_dim=F(20); f_small=F(13); f_tag=F(16)

def view_origin(area): 
    return area

# 视图布局: (left, top) 轮廓原点
FR = (70,  130)   # 正视图
SR = (470, 130)   # 侧视图
TP = (70,  470)   # 顶视图

def draw_box(d, ox, oy, wpx, hpx, color=(30,30,30), w=3):
    d.rectangle([ox,oy,ox+wpx,oy+hpx], outline=color, width=w)

# 绘制尺寸横线 (顶部/下方)
def dim_h(d, x1, x2, y, text, font, color=(0,0,0)):
    d.line([x1,y,x2,y], fill=color, width=2)
    for xx in (x1,x2): d.line([xx,y-7,xx,y+7], fill=color, width=2)
    tw = d.textlength(text, font=font)
    d.text(((x1+x2)/2 - tw/2, y-28), text, font=font, fill=color)

def dim_v(d, y1, y2, x, text, font, color=(0,0,0)):
    d.line([x,y1,x,y2], fill=color, width=2)
    for yy in (y1,y2): d.line([x-7,yy,x+7,yy], fill=color, width=2)
    tw = d.textlength(text, font=font)
    d.text((x+10,(y1+y2)/2 - 12), text, font=font, fill=color)

def extend_line(d, x1,x2,y,color=(90,90,90)):
    d.line([x1,y,x2,y], fill=color, width=1)

# ============ 标题 ============
d.text((70,30), "五件式弹卡收纳盒 · 三视图尺寸标注", font=f_title, fill=(20,20,20))
d.text((70,72), f"整体尺寸 {int(L)} × {int(W)} × {int(H)} mm · 壁厚 {T}mm · 顶部开口朝上 · 半高隔板", font=f_sub, fill=(70,70,70))

# ============ 正视图(前视) : 长300 × 高210, 前盖5条散热槽 ============
ox,oy = FR
wpx,hpx = int(L*SCALE), int(H*SCALE)
draw_box(d,ox,oy,wpx,hpx)
# 前盖散热槽
for x in front_x:
    sx = ox + int(x*SCALE)
    draw_box(d, sx, oy+int(front_z0*SCALE), int(vent_w*SCALE), int((front_z1-front_z0)*SCALE), color=(120,120,120), w=2)
# 底部底板(含底脚)
draw_box(d,ox,oy+int((H-15.2)*SCALE),wpx,int(15.2*SCALE), color=(90,90,90), w=2)
# 标注: 总长
extend_line(d, ox, ox+wpx, oy-35)
dim_h(d, ox, ox+wpx, oy-35, f"{int(L)}", f_dim)
d.text((ox-10, oy-70), "长", font=f_tag, fill=(40,40,40))
# 标注: 总高
extend_line(d, oy, oy+hpx, ox+wpx+35)
dim_v(d, oy, oy+hpx, ox+wpx+35, f"{int(H)}", f_dim)
d.text((ox+wpx+55, oy-8), "高", font=f_tag, fill=(40,40,40))
# 散热槽宽度标注(放大)
sx=front_x[2]; sy=front_z0
d.text((ox+int(L*SCALE)+8, oy+int(front_z0*SCALE)), "散热槽宽8", font=f_small, fill=(150,0,0))
# 壁厚标注
d.text((ox+int(L*SCALE)-150, oy+int(H*SCALE)-25), "壁厚2.2", font=f_small, fill=(150,0,0))
d.text((ox, oy+hpx+18), "正视图(前视)：长×高", font=f_tag, fill=(60,60,60))

# ============ 侧视图 : 宽210 × 高210, 侧板3条散热槽 ============
ox,oy = SR
wpx,hpx = int(W*SCALE), int(H*SCALE)
draw_box(d,ox,oy,wpx,hpx)
for x in side_w:
    sx = ox + int(x*SCALE)
    draw_box(d, sx, oy+int(side_z0*SCALE), int(vent_w*SCALE), int((side_z1-side_z0)*SCALE), color=(120,120,120), w=2)
draw_box(d,ox,oy+int((H-15.2)*SCALE),wpx,int(15.2*SCALE), color=(90,90,90), w=2)
extend_line(d, ox, ox+wpx, oy-35)
dim_h(d, ox, ox+wpx, oy-35, f"{int(W)}", f_dim)
d.text((ox-10, oy-70), "宽", font=f_tag, fill=(40,40,40))
extend_line(d, oy, oy+hpx, ox+wpx+35)
dim_v(d, oy, oy+hpx, ox+wpx+35, f"{int(H)}", f_dim)
d.text((ox+wpx+55, oy-8), "高", font=f_tag, fill=(40,40,40))
d.text((ox+int(W*SCALE)+8, oy+int(side_z0*SCALE)), "散热槽宽8", font=f_small, fill=(150,0,0))
d.text((ox, oy+hpx+18), "侧视图：宽×高", font=f_tag, fill=(60,60,60))

# ============ 顶视图(开口) : 长300 × 宽210, 隔板 ============
ox,oy = TP
wpx,hpx = int(L*SCALE), int(W*SCALE)
draw_box(d,ox,oy,wpx,hpx)
# 隔板(竖直条 X115.1..117.3 沿宽向)
sx=ox+int(div_x1*SCALE); sw=int((div_x2-div_x1)*SCALE)
draw_box(d,sx,oy,sw,hpx, color=(200,60,0), w=3)
d.text((ox+int(div_x2*SCALE)+6, oy+int(W*SCALE)*0.4), "隔板(半高)", font=f_small, fill=(200,60,0))
# 底榫位置点
for tx,tw in zip(tenon_x,tenon_w):
    px=ox+int(tx*SCALE); py=oy+int(tw*SCALE)
    d.ellipse([px-3,py-3,px+3,py+3], fill=(0,90,180))
# 标注 总长
extend_line(d, ox, ox+wpx, oy-35)
dim_h(d, ox, ox+wpx, oy-35, f"{int(L)}", f_dim)
d.text((ox-10, oy-70), "长", font=f_tag, fill=(40,40,40))
# 标注 总宽
extend_line(d, oy, oy+hpx, ox+wpx+35)
dim_v(d, oy, oy+hpx, ox+wpx+35, f"{int(W)}", f_dim)
d.text((ox+wpx+55, oy-8), "宽", font=f_tag, fill=(40,40,40))
# 隔板分区标注
xL2 = ox+int(div_x1*SCALE)
extend_line(d, ox, xL2, oy+hpx+30)
dim_h(d, ox, xL2, oy+hpx+30, "≈113(Mac mini区)", f_small)
extend_line(d, xL2+sw, ox+wpx, oy+hpx+55)
dim_h(d, xL2+sw, ox+wpx, oy+hpx+55, f"≈{int(L)-int(div_x2)}", f_small)
d.text((ox, oy+hpx+18+40), "顶视图(开口)：长×宽，隔板X=115把内部左右分开", font=f_tag, fill=(60,60,60))

# ============ 底部汇总 ============
notes = [
    "装配：底座总成 + 左/右侧板 + 前/后盖板(顶部开口卡扣安装)",
    "散热：前后盖板各5条竖槽(宽8×高125)、左右板各3条竖槽(宽8×高120)",
    "隔板：半高100mm，X=115 左侧区≈113mm 放Mac mini(200×110)",
    "连接：直榫定位/拎榫/弹性卡钩+固定卡槽/推入卡紧/一次卡紧/插入卡紧",
]
ny = H_IMG-150
d.text((70, ny), "装配与特征说明", font=f_tag, fill=(20,20,20))
for i,nt in enumerate(notes):
    d.text((90, ny+34+i*32), nt, font=f_small, fill=(60,60,60))

out = "/Users/zhaojian/code/fusion360/local_checkpoints/20261101_snapbox_5part/dimensions.png"
img.save(out)
print({"saved": True, "path": out, "size": img.size})
