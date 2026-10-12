"""デモ用の仮イメージ画像を生成する（外部写真素材の代替）。
本番では assets/img/photo/ 内の同名ファイルを実際の現場写真・購入素材に差し替えてください。
usage: python3 tools/generate_images.py
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = "assets/img/photo"
os.makedirs(OUT, exist_ok=True)
SS = 2  # スーパーサンプリング倍率


def noise(w, h, seed, octaves=6, base=4):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        g = rng.random((max(2, int(n * h / w)) + 1, n + 1)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.5
    return acc / tot


def lerp(a, b, t):
    return a + (b - a) * t


def vgrad(w, h, stops):
    """stops: [(pos, (r,g,b)), ...] 上から下へ"""
    y = np.linspace(0, 1, h)[:, None]
    out = np.zeros((h, w, 3), np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (y >= p0) & (y <= p1)
        t = np.clip((y - p0) / max(p1 - p0, 1e-6), 0, 1)
        col = np.array(c0, np.float32) + (np.array(c1, np.float32) - np.array(c0, np.float32)) * t[..., None]
        out = np.where(m[..., None], np.broadcast_to(col, (h, w, 3)) if col.shape[1] == 1 else col, out)
    return out


def glow(arr, cx, cy, r, color, strength=1.0):
    h, w, _ = arr.shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    g = np.exp(-d ** 2) * strength
    return arr + g[..., None] * np.array(color, np.float32)


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def finish(img, w, h, name, seed=0, grain=7, vignette=0.45, warm=True):
    img = img.resize((w, h), Image.LANCZOS)
    a = np.asarray(img, np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a *= (1 - vignette * np.clip(d - 0.35, 0, 1) ** 1.5)[..., None]
    if warm:  # シネマ調：シャドウを寒色、ハイライトを暖色に
        lum = a.mean(axis=2, keepdims=True) / 255
        a += (1 - lum) * np.array([-4, 0, 6]) + lum * np.array([8, 2, -8])
    rng = np.random.default_rng(seed + 99)
    a += rng.normal(0, grain, (h, w, 1))
    to_img(a).save(os.path.join(OUT, name), quality=80, optimize=True, progressive=True)
    print("saved", name)


# ---------- シルエット部品 ----------
def poly(draw, pts, ox, oy, s, fill, flip=False):
    draw.polygon([((-x if flip else x) * s + ox, y * s + oy) for x, y in pts], fill=fill)


def excavator(draw, ox, oy, s, fill, flip=False, arm=0.0):
    P = lambda pts: poly(draw, pts, ox, oy, s, fill, flip)
    # クローラー
    P([(-160, 0), (160, 0), (185, -20), (185, -45), (160, -62), (-160, -62), (-185, -45), (-185, -20)])
    P([(-120, -62), (120, -62), (120, -80), (-120, -80)])
    # 上部旋回体
    P([(-170, -80), (110, -80), (110, -185), (-120, -185), (-170, -150)])
    P([(-30, -185), (100, -185), (100, -300), (10, -300), (-30, -260)])  # キャブ
    # ブーム
    bx, by = 90, -170
    a1 = math.radians(-50 + arm * 10)
    l1 = 330
    ex, ey = bx + math.cos(a1) * l1, by + math.sin(a1) * l1
    a2 = math.radians(75 + arm * 20)
    l2 = 250
    fx, fy = ex + math.cos(a2) * l2, ey + math.sin(a2) * l2

    def beam(x0, y0, x1, y1, t0, t1):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        P([(x0 + nx * t0, y0 + ny * t0), (x1 + nx * t1, y1 + ny * t1), (x1 - nx * t1, y1 - ny * t1), (x0 - nx * t0, y0 - ny * t0)])

    beam(bx, by, ex, ey, 34, 24)
    beam(ex, ey, fx, fy, 20, 14)
    # バケット
    P([(fx - 30, fy - 10), (fx + 50, fy - 5), (fx + 70, fy + 60), (fx + 10, fy + 75), (fx - 35, fy + 30)])
    return fx, fy


def crane(draw, ox, oy, s, fill, flip=False, width=2):
    sx = lambda x: (-x if flip else x) * s + ox
    sy = lambda y: y * s + oy
    lw = max(1, int(width * s))
    H = 900
    for x in (-25, 25):
        draw.line([(sx(x), sy(0)), (sx(x), sy(-H))], fill=fill, width=lw * 2)
    for y in range(0, H, 50):
        draw.line([(sx(-25), sy(-y)), (sx(25), sy(-y - 50))], fill=fill, width=lw)
        draw.line([(sx(25), sy(-y)), (sx(-25), sy(-y - 50))], fill=fill, width=lw)
    # ジブ
    draw.line([(sx(-260), sy(-H)), (sx(780), sy(-H))], fill=fill, width=lw * 3)
    draw.line([(sx(-260), sy(-H + 30)), (sx(780), sy(-H + 30))], fill=fill, width=lw)
    for x in range(-260, 780, 40):
        draw.line([(sx(x), sy(-H)), (sx(x + 40), sy(-H + 30))], fill=fill, width=lw)
    draw.polygon([(sx(-25), sy(-H)), (sx(25), sy(-H)), (sx(0), sy(-H - 120))], fill=fill)
    draw.line([(sx(0), sy(-H - 120)), (sx(780), sy(-H))], fill=fill, width=lw)
    draw.line([(sx(0), sy(-H - 120)), (sx(-260), sy(-H))], fill=fill, width=lw)
    draw.rectangle([sx(-250), sy(-H + 30), sx(-170), sy(-H + 90)] if not flip else [sx(-170), sy(-H + 30), sx(-250), sy(-H + 90)], fill=fill)
    # 吊り荷
    hx = 520
    draw.line([(sx(hx), sy(-H + 30)), (sx(hx), sy(-H + 420))], fill=fill, width=lw)
    draw.rectangle(sorted_rect(sx(hx - 60), sy(-H + 420), sx(hx + 60), sy(-H + 450)), fill=fill)


def sorted_rect(x0, y0, x1, y1):
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def ridge(draw, w, h, base, amp, seed, fill, rough=0.5):
    rng = np.random.default_rng(seed)
    n = 40
    xs = np.linspace(-10, w + 10, n)
    ys = base + np.cumsum(rng.normal(0, amp * rough, n))
    ys = ys - (ys.mean() - base)
    ys += np.sin(np.linspace(0, math.pi * rng.uniform(1, 3), n)) * amp
    pts = list(zip(xs, ys)) + [(w + 10, h + 10), (-10, h + 10)]
    draw.polygon(pts, fill=fill)


def dust(arr, seed, count, color, ymin=0.3, size=2.0):
    h, w, _ = arr.shape
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(h * ymin, h)
        r = rng.uniform(0.5, size) * SS
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(40, 200)))
    m = np.asarray(img.filter(ImageFilter.GaussianBlur(1.2 * SS)), np.float32) / 255
    return arr + m[..., None] * np.array(color, np.float32)


def haze(arr, seed, y0, y1, color, strength):
    h, w, _ = arr.shape
    n = noise(w // 8, h // 8, seed, octaves=4, base=3)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    y = np.linspace(0, 1, h)[:, None]
    band = np.clip(1 - np.abs((y - (y0 + y1) / 2) / ((y1 - y0) / 2)), 0, 1)
    m = band * n * strength
    return arr * (1 - m[..., None]) + np.array(color, np.float32) * m[..., None]


# ---------- シーン ----------
def scene_dusk_site(w, h, name, seed=1, sun=(0.72, 0.52), machine=True, crane_on=True, flip=False, palette="dusk"):
    W, H = w * SS, h * SS
    if palette == "dusk":
        sky = vgrad(W, H, [(0, (18, 20, 30)), (0.35, (60, 44, 48)), (0.55, (200, 92, 36)), (0.62, (255, 150, 60)), (1, (40, 26, 20))])
        sunc, ground = (255, 140, 40), (14, 12, 13)
    elif palette == "morning":
        sky = vgrad(W, H, [(0, (70, 92, 120)), (0.45, (170, 170, 168)), (0.6, (240, 196, 140)), (1, (60, 50, 44))])
        sunc, ground = (255, 200, 120), (28, 26, 26)
    else:  # steel
        sky = vgrad(W, H, [(0, (24, 28, 34)), (0.5, (86, 92, 100)), (0.62, (150, 140, 128)), (1, (30, 30, 32))])
        sunc, ground = (255, 160, 80), (18, 18, 20)
    sky = glow(sky, W * sun[0], H * sun[1], W * 0.08, sunc, 1.2)
    sky = glow(sky, W * sun[0], H * sun[1], W * 0.35, sunc, 0.35)
    sky = haze(sky, seed, 0.1, 0.5, (90, 70, 70), 0.25)
    img = to_img(sky)
    d = ImageDraw.Draw(img)
    far = tuple(int(c * 0.9 + g * 0.1) for c, g in zip((70, 50, 48), ground))
    ridge(d, W, H, H * 0.6, H * 0.02, seed + 1, far)
    if crane_on:
        crane(d, W * (0.2 if not flip else 0.85), H * 0.63, H / 2100, (36, 28, 30), flip=flip)
    mid = tuple(int(c) for c in (38, 30, 30))
    ridge(d, W, H, H * 0.68, H * 0.03, seed + 2, mid)
    if machine:
        excavator(d, W * (0.62 if not flip else 0.38), H * 0.84, H / 900, ground, flip=not flip)
    ridge(d, W, H, H * 0.86, H * 0.025, seed + 3, ground, rough=0.3)
    arr = np.asarray(img, np.float32)
    arr = haze(arr, seed + 7, 0.6, 0.95, (160, 90, 50), 0.22)
    arr = dust(arr, seed, 260, (255, 170, 90), ymin=0.45)
    finish(to_img(arr), w, h, name, seed)


def scene_wall(w, h, name, seed=2, kind="brick", light=(0.8, 0.2), tint=(1.0, 0.92, 0.85)):
    """レンガ・ブロック・タイル壁の斜光表現"""
    W, H = w * SS, h * SS
    base = noise(W // 2, H // 2, seed, octaves=7, base=8)
    base = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(seed)
    if kind == "brick":
        bw, bh, joint = 230 * SS / 2, 76 * SS / 2, 9 * SS / 2
        col0 = np.array([150, 70, 44]) * np.array(tint)
    elif kind == "block":
        bw, bh, joint = 390 * SS / 2, 190 * SS / 2, 10 * SS / 2
        col0 = np.array([150, 148, 142]) * np.array(tint)
    else:  # tile
        bw, bh, joint = 300 * SS / 2, 300 * SS / 2, 6 * SS / 2
        col0 = np.array([196, 186, 172]) * np.array(tint)
    # 遠近：上が奥
    persp = 1 + (yy / H) * 0.6
    u = (xx - W / 2) / persp + W / 2
    v = yy * (1 + yy / H * 0.3)
    row = np.floor(v / bh)
    off = (row % 2) * bw / 2 if kind != "tile" else 0
    col = np.floor((u + off) / bw)
    fu = (u + off) - col * bw
    fv = v - row * bh
    jm = ((fu < joint) | (fv < joint)).astype(np.float32)
    rid = (np.sin(row * 12.9898 + col * 78.233) * 43758.5453) % 1
    shade = 0.82 + rid[..., None] * 0.3
    arr = col0[None, None, :] * shade * (0.75 + base[..., None] * 0.45)
    mortar = np.array([90, 88, 84]) if kind == "brick" else np.array([70, 70, 70])
    arr = arr * (1 - jm[..., None]) + mortar * (0.7 + base[..., None] * 0.5) * jm[..., None]
    # 斜光
    lx, ly = W * light[0], H * light[1]
    dd = np.sqrt((xx - lx) ** 2 + (yy - ly) ** 2) / (W * 0.9)
    arr *= (1.25 - dd * 0.9)[..., None]
    arr = np.clip(arr, 0, 255)
    finish(to_img(arr), w, h, name, seed, vignette=0.55)


def scene_scaffold(w, h, name, seed=3):
    """足場（とび工事）のシルエット"""
    W, H = w * SS, h * SS
    sky = vgrad(W, H, [(0, (30, 44, 66)), (0.55, (150, 150, 160)), (0.8, (240, 170, 110)), (1, (250, 130, 60))])
    sky = glow(sky, W * 0.3, H * 0.85, W * 0.25, (255, 140, 50), 0.6)
    img = to_img(sky)
    d = ImageDraw.Draw(img)
    c = (20, 20, 24)
    # 建物
    d.rectangle([W * 0.18, H * 0.12, W * 0.92, H], fill=(46, 46, 52))
    for i in range(10):
        for j in range(14):
            x = W * 0.2 + j * W * 0.05
            y = H * 0.15 + i * H * 0.085
            if x < W * 0.9:
                d.rectangle([x, y, x + W * 0.03, y + H * 0.05], fill=(70, 70, 78) if (i + j) % 5 else (230, 170, 100))
    # 足場
    cols = np.linspace(W * 0.14, W * 0.96, 12)
    for x in cols:
        d.line([(x, H * 0.06), (x, H)], fill=c, width=5 * SS)
    for y in np.linspace(H * 0.08, H, 9):
        d.line([(cols[0], y), (cols[-1], y)], fill=c, width=5 * SS)
        d.rectangle([cols[0], y, cols[-1], y + 10 * SS], fill=c)
    for i in range(len(cols) - 1):
        for k, y in enumerate(np.linspace(H * 0.08, H, 9)[:-1]):
            if (i + k) % 2 == 0:
                d.line([(cols[i], y), (cols[i + 1], y + (H * 0.115))], fill=c, width=3 * SS)
    # 人物シルエット（作業員）
    for px, py in [(0.42, 0.315), (0.71, 0.55)]:
        x, y = W * px, H * py
        s = H / 900
        d.ellipse([x - 12 * s, y - 92 * s, x + 12 * s, y - 68 * s], fill=c)
        d.polygon([(x - 26 * s, y - 92 * s), (x + 26 * s, y - 92 * s), (x + 20 * s, y - 80 * s), (x - 20 * s, y - 80 * s)], fill=c)
        d.rectangle([x - 16 * s, y - 68 * s, x + 16 * s, y - 25 * s], fill=c)
        d.polygon([(x - 16 * s, y - 25 * s), (x - 4 * s, y - 25 * s), (x - 8 * s, y + 8 * s), (x - 20 * s, y + 8 * s)], fill=c)
        d.polygon([(x + 4 * s, y - 25 * s), (x + 16 * s, y - 25 * s), (x + 22 * s, y + 8 * s), (x + 10 * s, y + 8 * s)], fill=c)
    arr = dust(np.asarray(img, np.float32), seed, 120, (255, 180, 110), ymin=0.5)
    finish(to_img(arr), w, h, name, seed)


def scene_interior(w, h, name, seed=4):
    """ハウスクリーニング：光の差し込む明るい室内"""
    W, H = w * SS, h * SS
    arr = vgrad(W, H, [(0, (232, 228, 222)), (0.62, (214, 208, 200)), (0.63, (176, 150, 120)), (1, (140, 112, 86))])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 床の木目
    floor = yy > H * 0.63
    grain = noise(W // 4, H // 4, seed, 5, 6)
    grain = np.asarray(Image.fromarray((grain * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    planks = ((xx + (yy - H * 0.63) * (xx / W - 0.5) * 3) % (W / 9) < 3 * SS)
    arr = np.where((floor & planks)[..., None], arr * 0.8, arr)
    arr = np.where(floor[..., None], arr * (0.9 + grain[..., None] * 0.2), arr)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # 窓
    wx0, wx1, wy0, wy1 = W * 0.52, W * 0.86, H * 0.12, H * 0.6
    d.rectangle([wx0, wy0, wx1, wy1], fill=(255, 250, 240))
    d.rectangle([wx0, wy0, wx1, wy1], outline=(200, 194, 186), width=8 * SS)
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(200, 194, 186), width=6 * SS)
    # ソファ風のブロック
    d.rounded_rectangle([W * 0.08, H * 0.48, W * 0.42, H * 0.68], radius=20 * SS, fill=(90, 86, 82))
    d.rounded_rectangle([W * 0.06, H * 0.42, W * 0.12, H * 0.68], radius=14 * SS, fill=(80, 76, 72))
    d.rounded_rectangle([W * 0.38, H * 0.42, W * 0.44, H * 0.68], radius=14 * SS, fill=(80, 76, 72))
    # 観葉植物
    d.rectangle([W * 0.9, H * 0.5, W * 0.96, H * 0.66], fill=(60, 56, 52))
    for i in range(14):
        a = i / 14 * math.pi
        d.ellipse([W * 0.93 + math.cos(a) * W * 0.04 - 24 * SS, H * 0.42 - math.sin(a) * H * 0.1 - 10 * SS,
                   W * 0.93 + math.cos(a) * W * 0.04 + 24 * SS, H * 0.42 - math.sin(a) * H * 0.1 + 10 * SS], fill=(70, 100, 70))
    arr = np.asarray(img, np.float32)
    # 光の帯（床への差し込み）
    beam = np.zeros((H, W), np.float32)
    bimg = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bimg)
    bd.polygon([(wx0, wy0), (wx1, wy0), (wx1 - W * 0.1, H), (wx0 - W * 0.42, H)], fill=60)
    beam = np.asarray(bimg.filter(ImageFilter.GaussianBlur(40 * SS)), np.float32) / 255
    arr = arr + beam[..., None] * np.array([255, 220, 170])
    arr = dust(arr, seed, 160, (255, 240, 210), ymin=0.1, size=1.4)
    finish(to_img(arr), w, h, name, seed, grain=4, vignette=0.3)


def scene_building(w, h, name, seed=5):
    """清掃管理：オフィスビル外観（見上げ）"""
    W, H = w * SS, h * SS
    arr = vgrad(W, H, [(0, (40, 70, 110)), (0.6, (150, 180, 210)), (1, (230, 220, 210))])
    arr = glow(arr, W * 0.85, H * 0.1, W * 0.3, (255, 200, 140), 0.5)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # 見上げのビル（台形）
    d.polygon([(W * 0.12, H), (W * 0.88, H), (W * 0.68, 0), (W * 0.32, 0)], fill=(40, 46, 56))
    for i in range(26):
        t0, t1 = i / 26, (i + 0.78) / 26
        y0, y1 = H * (1 - t0), H * (1 - t1)
        l0, r0 = lerp(W * 0.12, W * 0.32, t0), lerp(W * 0.88, W * 0.68, t0)
        l1, r1 = lerp(W * 0.12, W * 0.32, t1), lerp(W * 0.88, W * 0.68, t1)
        for j in range(8):
            a, b = j / 8 + 0.01, (j + 1) / 8 - 0.01
            refl = 90 + int(80 * math.sin(i * 0.3 + j * 0.9) ** 2)
            c = (refl - 30, refl, refl + 40)
            d.polygon([(lerp(l0, r0, a), y0), (lerp(l0, r0, b), y0), (lerp(l1, r1, b), y1), (lerp(l1, r1, a), y1)], fill=c)
    # ゴンドラ
    gy = H * 0.42
    gl, gr = lerp(W * 0.12, W * 0.32, 0.58) + W * 0.06, lerp(W * 0.88, W * 0.68, 0.58) - W * 0.12
    d.line([(gl + 20 * SS, 0), (gl + 20 * SS, gy)], fill=(30, 30, 30), width=2 * SS)
    d.line([(gl + 200 * SS, 0), (gl + 200 * SS, gy)], fill=(30, 30, 30), width=2 * SS)
    d.rectangle([gl, gy, gl + 220 * SS, gy + 40 * SS], fill=(255, 116, 0))
    arr = np.asarray(img, np.float32)
    finish(to_img(arr), w, h, name, seed, vignette=0.35)


def scene_concrete(w, h, name, seed=6, dark=True):
    """コンクリート打放しテクスチャ"""
    W, H = w * SS, h * SS
    n = noise(W // 2, H // 2, seed, 8, 6)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    base = 40 if dark else 150
    arr = (base + n * (40 if dark else 70))[..., None] * np.array([1.0, 0.98, 0.95])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 型枠割付とセパ穴
    pw, ph = W / 4, H / 3
    jm = ((xx % pw) < 2 * SS) | ((yy % ph) < 2 * SS)
    arr = np.where(jm[..., None], arr * 0.7, arr)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    for i in range(5):
        for j in range(4):
            x, y = (i * 2 + 1) * pw / 2, (j * 2 + 1) * ph / 2 - ph / 4
            r = 7 * SS
            d.ellipse([x - r, y - r, x + r, y + r], fill=(int(base * 0.6),) * 3)
    arr = np.asarray(img, np.float32)
    arr = glow(arr, W * 0.2, H * 0.1, W * 0.6, (255, 120, 30) if dark else (255, 220, 180), 0.25)
    finish(to_img(arr), w, h, name, seed, vignette=0.5)


def scene_road(w, h, name, seed=7):
    """道路・舗装工事（パース）"""
    W, H = w * SS, h * SS
    sky = vgrad(W, H, [(0, (60, 80, 110)), (0.38, (230, 180, 130)), (0.42, (90, 80, 76)), (1, (40, 38, 38))])
    sky = glow(sky, W * 0.5, H * 0.38, W * 0.2, (255, 150, 60), 0.9)
    img = to_img(sky)
    d = ImageDraw.Draw(img)
    vx, vy = W * 0.5, H * 0.4
    d.polygon([(vx - 6 * SS, vy), (vx + 6 * SS, vy), (W * 1.1, H), (-W * 0.1, H)], fill=(52, 50, 50))
    d.polygon([(vx - 2 * SS, vy), (vx + 2 * SS, vy), (W * 0.55, H), (W * 0.45, H)], fill=(66, 64, 62))
    for k in range(12):
        t0 = (k / 12) ** 2
        t1 = ((k + 0.5) / 12) ** 2
        y0, y1 = lerp(vy, H, t0), lerp(vy, H, t1)
        ww0, ww1 = lerp(1, 18, t0) * SS, lerp(1, 18, t1) * SS
        d.polygon([(vx - ww0, y0), (vx + ww0, y0), (vx + ww1, y1), (vx - ww1, y1)], fill=(230, 200, 120))
    # 三角コーン
    for k, side in [(3, -1), (5, -1), (7, -1), (9, -1)]:
        t = (k / 12) ** 2
        y = lerp(vy, H, t)
        x = vx + side * lerp(10, W * 0.42, t)
        s = lerp(0.1, 1.6, t) * SS
        d.polygon([(x - 18 * s, y), (x + 18 * s, y), (x + 5 * s, y - 60 * s), (x - 5 * s, y - 60 * s)], fill=(255, 110, 20))
        d.rectangle([x - 12 * s, y - 34 * s, x + 12 * s, y - 24 * s], fill=(240, 240, 240))
    excavator(d, W * 0.78, H * 0.62, H / 1800, (20, 18, 18), flip=True, arm=0.5)
    arr = np.asarray(img, np.float32)
    arr = haze(arr, seed, 0.3, 0.6, (200, 150, 110), 0.3)
    finish(to_img(arr), w, h, name, seed)


def scene_exterior(w, h, name, seed=8):
    """外構工事：住宅の門まわり・ブロック塀と植栽"""
    W, H = w * SS, h * SS
    arr = vgrad(W, H, [(0, (120, 150, 180)), (0.5, (220, 214, 200)), (1, (200, 190, 176))])
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    # 家
    d.rectangle([W * 0.25, H * 0.18, W * 0.95, H * 0.7], fill=(236, 232, 226))
    d.polygon([(W * 0.2, H * 0.2), (W * 1.0, H * 0.2), (W * 0.95, H * 0.14), (W * 0.25, H * 0.14)], fill=(48, 48, 52))
    d.rectangle([W * 0.6, H * 0.28, W * 0.86, H * 0.5], fill=(80, 96, 110))
    d.rectangle([W * 0.32, H * 0.36, W * 0.44, H * 0.7], fill=(120, 90, 66))
    # アプローチ（タイル）
    d.polygon([(W * 0.33, H * 0.7), (W * 0.45, H * 0.7), (W * 0.62, H), (W * 0.12, H)], fill=(190, 180, 166))
    for k in range(1, 8):
        t = (k / 8) ** 1.3
        y = lerp(H * 0.7, H, t)
        d.line([(lerp(W * 0.33, W * 0.12, t), y), (lerp(W * 0.45, W * 0.62, t), y)], fill=(150, 140, 128), width=2 * SS)
    # ブロック塀
    d.rectangle([W * 0.55, H * 0.6, W * 1.0, H * 0.82], fill=(170, 166, 160))
    for i in range(4):
        y = H * 0.6 + i * H * 0.055
        d.line([(W * 0.55, y), (W, y)], fill=(130, 126, 120), width=2 * SS)
        for j in range(10):
            x = W * 0.55 + j * W * 0.06 + (i % 2) * W * 0.03
            d.line([(x, y), (x, y + H * 0.055)], fill=(130, 126, 120), width=2 * SS)
    d.rectangle([W * 0.55, H * 0.6, W * 1.0, H * 0.615], fill=(110, 106, 100))
    # 植栽
    rng = np.random.default_rng(seed)
    for _ in range(90):
        x, y = rng.uniform(0, W * 0.22), rng.uniform(H * 0.35, H * 0.9)
        r = rng.uniform(20, 60) * SS
        g = int(rng.uniform(70, 120))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(g - 30, g + 10, g - 40))
    d.rectangle([W * 0.05, H * 0.55, W * 0.07, H * 0.95], fill=(70, 50, 40))
    arr = np.asarray(img, np.float32)
    arr = glow(arr, W * 0.9, H * 0.0, W * 0.5, (255, 200, 140), 0.3)
    finish(to_img(arr), w, h, name, seed, grain=5, vignette=0.35)


if __name__ == "__main__":
    scene_dusk_site(2400, 1350, "hero.jpg", seed=11)
    scene_dusk_site(1600, 1000, "about.jpg", seed=21, palette="steel", flip=True)
    scene_road(1600, 1000, "service-civil.jpg", seed=31)
    scene_wall(1600, 1000, "service-block.jpg", seed=41, kind="brick")
    scene_interior(1600, 1000, "service-cleaning.jpg", seed=51)
    scene_scaffold(1600, 1000, "service-tobi.jpg", seed=61)
    scene_building(1600, 1000, "service-maintenance.jpg", seed=71)
    scene_concrete(2000, 1200, "philosophy.jpg", seed=81, dark=True)
    scene_exterior(1200, 900, "works-01.jpg", seed=91)
    scene_dusk_site(1200, 900, "works-02.jpg", seed=92, palette="morning", crane_on=False)
    scene_wall(1200, 900, "works-03.jpg", seed=93, kind="block", light=(0.2, 0.1))
    scene_scaffold(1200, 900, "works-04.jpg", seed=94)
    scene_wall(1200, 900, "works-05.jpg", seed=95, kind="tile", light=(0.7, 0.0))
    scene_road(1200, 900, "works-06.jpg", seed=96)
    scene_concrete(1600, 900, "page-header.jpg", seed=97, dark=True)
