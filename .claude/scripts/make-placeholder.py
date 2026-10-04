#!/usr/bin/env python3
"""Genere un visuel de couverture PNG, sans aucune dependance ni acces reseau.

Les couleurs suivent la charte de Goûter Gourmand.

Filet de securite de fetch-image.sh. L'environnement cloud des routines bloque
les domaines commerciaux via son proxy egress, donc le telechargement d'une
photo y echoue par conception et la skill publiait alors l'article SANS AUCUN
visuel.

Pourquoi du PNG et pas du SVG : `layouts/partials/head.html` construit l'og:image
a partir du champ `image` du frontmatter, et aucun reseau social ne sait lire un
SVG en og:image. Un placeholder SVG casserait donc le partage social. zlib et
struct suffisent a ecrire un PNG valide, ils sont dans la stdlib.

Usage : make-placeholder.py <slug> <chemin de sortie .png> [largeur] [hauteur]
"""
import sys, zlib, struct

# 1200x630 : format attendu par les og:image, et exploitable en hero (recadre)
W, H = 1200, 630

# Palettes choisies de facon stable a partir du slug.
# Charte du blog : chocolat #3B2019, framboise #E2485C, miel #E4A93C, porcelaine #3F6C8E.
PALETTES = [
    ((92, 52, 40),   (59, 32, 25)),    # chocolat
    ((226, 72, 92),  (184, 45, 64)),   # framboise
    ((228, 169, 60), (160, 112, 30)),  # miel
    ((63, 108, 142), (40, 72, 98)),    # porcelaine
]

def build(slug, w=W, h=H):
    seed = zlib.crc32(slug.encode("utf-8"))
    c1, c2 = PALETTES[seed % len(PALETTES)]
    # centre du halo, deplace selon le slug pour que deux articles different
    hx = 0.18 + (seed % 5) * 0.16
    hy = 0.16 + ((seed >> 3) % 3) * 0.22

    rows = []
    for y in range(h):
        fy = y / (h - 1)
        row = bytearray()
        row.append(0)  # filtre PNG 0 (None) en tete de chaque scanline
        for x in range(w):
            fx = x / (w - 1)
            # degradé diagonal
            t = (fx + fy) / 2
            r = c1[0] + (c2[0] - c1[0]) * t
            g = c1[1] + (c2[1] - c1[1]) * t
            b = c1[2] + (c2[2] - c1[2]) * t
            # halo clair, adoucit le rendu et evite l'aplat mort
            dx, dy = fx - hx, fy - hy
            d = (dx * dx + dy * dy) ** 0.5
            glow = max(0.0, 1.0 - d / 0.95) ** 2 * 0.20
            r += (255 - r) * glow
            g += (255 - g) * glow
            b += (255 - b) * glow
            row += bytes((int(r), int(g), int(b)))
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: make-placeholder.py <slug> <out.png> [w] [h]", file=sys.stderr)
        sys.exit(1)
    slug, out = sys.argv[1], sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 else W
    h = int(sys.argv[4]) if len(sys.argv) > 4 else H
    with open(out, "wb") as f:
        f.write(build(slug, w, h))
    print(out)
