"""名刺画像から株式会社RISEのロゴを切り出し、白背景を透過にする。
形状・配色は変更せず、白→透明の「カラー・トゥ・アルファ」処理のみを行う。
usage: python3 tools/extract_logo.py <名刺1.jpg> <名刺2.jpg>
"""
import sys
import numpy as np
from PIL import Image

OUT = "assets/img/"


def white_to_alpha(img, scale=3, floor=0.10, clear=None):
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    rgb = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    a = (1.0 - rgb).max(axis=2)
    a = np.clip((a - floor) / (1.0 - floor), 0, 1)
    safe = np.where(a > 0, a, 1)[..., None]
    col = np.clip((rgb - (1 - a[..., None])) / safe, 0, 1)
    if clear:  # 名刺の透かし模様が入り込む領域を除去 (x0, y0, x1, y1) 切り出し前座標
        x0, y0, x1, y1 = (v * scale for v in clear)
        a[y0:y1, x0:x1] = 0
    out = np.dstack([col, a]) * 255
    im = Image.fromarray(out.astype(np.uint8), "RGBA")
    return im.crop(im.getbbox())


def main(card1, card2):
    c1 = Image.open(card1)
    c2 = Image.open(card2)
    # 横組みロゴ（名刺表面）
    horiz = white_to_alpha(c1.crop((42, 27, 412, 160)), clear=(218, 0, 370, 63))
    horiz.save(OUT + "logo-horizontal.png", optimize=True)
    # 縦組みロゴ（名刺裏面）
    vert = white_to_alpha(c2.crop((10, 25, 352, 245)))
    vert.save(OUT + "logo-vertical.png", optimize=True)
    # シンボルマークのみ（ファビコン用）
    mark = white_to_alpha(c2.crop((70, 28, 240, 140)))
    mark.save(OUT + "logo-mark.png", optimize=True)
    fav = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    m = mark.copy()
    m.thumbnail((236, 236), Image.LANCZOS)
    fav.paste(m, ((256 - m.width) // 2, (256 - m.height) // 2), m)
    fav.save(OUT + "favicon.png", optimize=True)
    for n, im in [("horizontal", horiz), ("vertical", vert), ("mark", mark)]:
        print(n, im.size)


if __name__ == "__main__":
    main(*sys.argv[1:3])
