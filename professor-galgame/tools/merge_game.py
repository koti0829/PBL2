# -*- coding: utf-8 -*-
# ch1〜ch4.json を game_complete.json へ合体する(WORKFLOW.md「5. 最後の統合」準拠)。
# エディタのノード同士が重ならないよう、座標を拡大しつつ章ごとに縦の帯へ動的パッキングする。
#
# 実行: professor-galgame フォルダで `python3 tools/merge_game.py`
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FILES = ["ch1.json", "ch2.json", "ch3.json", "ch4.json"]
SCALE_X, SCALE_Y = 1.5, 1.8
CHAPTER_GAP = 500
BOX_W, BOX_H = 240, 180


def px(v):
    m = re.match(r"(-?[\d.]+)", str(v))
    return float(m.group(1)) if m else 0.0


def resolve_overlaps(coords, box_w=BOX_W, box_h=BOX_H, pad=10, max_iter=50):
    keys = list(coords.keys())
    for _ in range(max_iter):
        moved = False
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ki, kj = keys[i], keys[j]
                dx = coords[kj][0] - coords[ki][0]
                dy = coords[kj][1] - coords[ki][1]
                if abs(dx) < box_w and abs(dy) < box_h:
                    moved = True
                    overlap_x = box_w - abs(dx)
                    overlap_y = box_h - abs(dy)
                    if overlap_x < overlap_y:
                        shift = overlap_x / 2 + pad
                        sign = 1 if dx >= 0 else -1
                        if dx == 0:
                            sign = 1 if j % 2 == 0 else -1
                        coords[kj][0] += sign * shift
                        coords[ki][0] -= sign * shift
                    else:
                        shift = overlap_y / 2 + pad
                        sign = 1 if dy >= 0 else -1
                        if dy == 0:
                            sign = 1
                        coords[kj][1] += sign * shift
                        coords[ki][1] -= sign * shift
        if not moved:
            break


def main():
    merged = None
    cursor_y = 0
    all_scaled = {}

    for fname in FILES:
        with open(BASE / fname, encoding="utf-8") as f:
            data = json.load(f)

        scaled = {k: [px(v[0]) * SCALE_X, px(v[1]) * SCALE_Y] for k, v in data["blocks"].items()}
        min_y = min(y for _, y in scaled.values())
        offset = cursor_y - min_y
        for k in scaled:
            scaled[k][1] += offset
        cursor_y = max(y for _, y in scaled.values()) + CHAPTER_GAP
        all_scaled.update(scaled)

        if merged is None:
            merged = data
            continue
        for key, val in data.items():
            if key in ("parameters", "blocks"):
                continue
            assert key not in merged, f"block collision: {key}"
            merged[key] = val

    resolve_overlaps(all_scaled)
    merged["blocks"] = {k: [f"{int(v[0])}px", f"{int(v[1])}px", "block", False] for k, v in all_scaled.items()}

    out = BASE / "game_complete.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    n_blocks = len([k for k in merged if k not in ("parameters", "blocks")])
    print(f"game_complete.json written: {n_blocks} story blocks, {len(merged['blocks'])} editor-position entries")

    overlaps = 0
    items = list(all_scaled.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (_, (x1, y1)), (_, (x2, y2)) = items[i], items[j]
            if abs(x1 - x2) < BOX_W and abs(y1 - y2) < BOX_H:
                overlaps += 1
    print(f"layout overlap check: {overlaps} pair(s)")


if __name__ == "__main__":
    main()
