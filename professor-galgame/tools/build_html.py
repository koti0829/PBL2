# -*- coding: utf-8 -*-
# game_complete.json から単体で動くHTMLを生成する。
# 公式doc(Step1-3)どおりの構成: #tuesday の div → tuesday.js インライン → load_story('data', <obj>)。
# load_story の 'data' 経路は XHR を使わないため file:// でもCORSエラーにならない。
#
# index.html          : 画像は data/... の相対パス参照のまま(軽い。フォルダごと配布)
# game_standalone.html: 画像もbase64で埋め込んだ完全1ファイル版
#
# 実行: professor-galgame フォルダで
#   python3 tools/merge_game.py   ← 先にこちらを実行して game_complete.json を最新化
#   python3 tools/build_html.py
import base64
import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ENGINE = Path(__file__).resolve().parent / "vendor" / "tuesday.js"

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}

# プレイ領域(#tuesday)は縦横比 3:2 の固定サイズにし、CSS transform:scale() で
# ウィンドウ/画面に合わせて拡大縮小する(レターボックス方式)。JSONの位置指定は
# すべて%指定なので、ステージのサイズが常に一定ならレイアウトは崩れない。
STAGE_W = 1200
STAGE_H = 800

HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, maximum-scale=1, user-scalable=no">
<title>教授Galgame</title>
<style>
  html, body {
    margin:0; padding:0; width:100%; height:100%;
    background:#000; overflow:hidden;
    overscroll-behavior:none; touch-action:manipulation;
    -webkit-user-select:none; user-select:none;
  }
  #tuesday {
    width:（STAGE_W）px; height:（STAGE_H）px;
    position:fixed; top:50%; left:50%;
    transform:translate(-50%,-50%) scale(1);
    transform-origin:center center;
    background:#000;
  }
  #rotate_notice {
    position:fixed; inset:0; z-index:100000; display:none;
    align-items:center; justify-content:center; text-align:center;
    background:#0e0f17; color:#f2f2f2; padding:32px; box-sizing:border-box;
    font-family:system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;
  }
</style>
</head>
<body>
<!-- 表示領域(固定サイズ。JSでウィンドウに合わせて拡大縮小する) -->
<div id="tuesday"></div>

<!-- スマホ縦持ち時の案内 -->
<div id="rotate_notice">
  <div>
    <div style="font-size:42px;margin-bottom:16px">📱↻</div>
    <div style="font-size:18px;line-height:1.8">画面を横向きにすると<br>広く表示されます</div>
  </div>
</div>

<!--
  Tuesday JS visual novel engine (https://github.com/Kirilllive/tuesday-js)
  Copyright Kirill Live, licensed under the Apache License, Version 2.0
  http://www.apache.org/licenses/LICENSE-2.0
-->
<script>
// file:// で localStorage が使えない環境でもエンジンが停止しないようにする最小限の保険
（LOCALSTORAGE_SHIM）
</script>
<script>
（ENGINE）
</script>
<script>
load_story('data', （STORY）);
</script>
<script>
（STAGE_FIT）
</script>
<script>
（START_GATE）
</script>
</body>
</html>
"""

# ウィンドウ/画面のサイズに関わらず、プレイ領域を常に同じ縦横比・同じ内部レイアウトで
# 表示するための拡大縮小。はみ出す分は黒帯(レターボックス)になる。
# スマホ縦持ちでは文字が小さくなりすぎるため、横向きへの案内を別途表示する。
STAGE_FIT = """(function(){
  var STAGE_W = （STAGE_W）, STAGE_H = （STAGE_H）;
  var stage = document.getElementById('tuesday');
  var notice = document.getElementById('rotate_notice');
  function fit(){
    var vw = window.innerWidth, vh = window.innerHeight;
    var scale = Math.min(vw / STAGE_W, vh / STAGE_H);
    stage.style.transform = 'translate(-50%,-50%) scale(' + scale + ')';
    var portrait = vh > vw;
    var small = Math.min(vw, vh) < 820;
    notice.style.display = (portrait && small) ? 'flex' : 'none';
  }
  window.addEventListener('resize', fit);
  window.addEventListener('orientationchange', fit);
  fit();
})();"""

# ブラウザは「ユーザーが操作するまで音を鳴らしてはいけない」という制限があり、
# 読み込み直後のタイトル画面ではOPのBGMがブロックされる。
# 1枚かぶせて1クリックもらうことで制限を解除し、OPから正常に鳴らす。
START_GATE = """(function(){
  var gate = document.createElement('div');
  gate.setAttribute('role', 'button');
  gate.setAttribute('tabindex', '0');
  gate.setAttribute('aria-label', 'クリックして開始');
  gate.style.cssText = [
    'position:fixed', 'inset:0', 'z-index:99999',
    'display:flex', 'align-items:center', 'justify-content:center',
    'background:#0e0f17', 'color:#f2f2f2',
    'font-family:system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif',
    'font-size:clamp(16px,3vw,26px)', 'letter-spacing:.08em',
    'cursor:pointer', 'user-select:none', '-webkit-user-select:none'
  ].join(';');
  gate.innerHTML = '<div style="text-align:center;line-height:2">'
    + '<div style="font-size:clamp(20px,4.5vw,40px);font-weight:700;margin-bottom:.6em">教授Galgame</div>'
    + '<div>画面をクリックして開始</div>'
    + '<div style="font-size:.62em;opacity:.6;margin-top:1.2em">音が出ます。音量にご注意ください</div>'
    + '</div>';

  var done = false;
  function start(){
    if (done) return;
    done = true;
    var m = document.getElementById('tue_bg_music');
    if (m && m.paused && m.src) { var p = m.play(); if (p && p.catch) p.catch(function(){}); }
    gate.remove();
  }
  gate.addEventListener('click', start);
  gate.addEventListener('keydown', function(e){
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); start(); }
  });

  function attach(){ document.body.appendChild(gate); gate.focus(); }
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', attach); }
  else { attach(); }
})();"""

SHIM = """(function(){
  try { window.localStorage.getItem('__t'); }
  catch (e) {
    var mem = {};
    try {
      Object.defineProperty(window, 'localStorage', { value: {
        getItem: function(k){ return Object.prototype.hasOwnProperty.call(mem,k) ? mem[k] : null; },
        setItem: function(k,v){ mem[k] = String(v); },
        removeItem: function(k){ delete mem[k]; },
        clear: function(){ mem = {}; }
      }, configurable: true });
    } catch (e2) {}
  }
})();"""


def collect_image_paths(obj, found):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("background_image", "url", "art") and isinstance(v, str) and v.startswith("data/"):
                found.add(v)
            else:
                collect_image_paths(v, found)
    elif isinstance(obj, list):
        for it in obj:
            collect_image_paths(it, found)


def inline_images(obj, index_map):
    """画像パスを base 配列の 1-based インデックス(数値)へ置換する。
    エンジンの art_data() が数値を story_json.base[n-1] として解決するため、
    同じ画像が何百ノードに出てきてもデータ本体は1回しか持たない。"""
    if isinstance(obj, dict):
        return {k: (index_map.get(v, v) if isinstance(v, str) else inline_images(v, index_map)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [inline_images(it, index_map) for it in obj]
    return obj


def render(story_obj, engine_src):
    story_js = json.dumps(story_obj, ensure_ascii=False, separators=(",", ":"))
    # </script> がJSON文字列内に現れてもHTMLを壊さないようにする
    story_js = story_js.replace("</", "<\\/")
    html = HEAD.replace("（LOCALSTORAGE_SHIM）", SHIM)
    html = html.replace("（ENGINE）", engine_src)
    html = html.replace("（STORY）", story_js)
    html = html.replace("（STAGE_FIT）", STAGE_FIT)
    html = html.replace("（START_GATE）", START_GATE)
    html = html.replace("（STAGE_W）", str(STAGE_W)).replace("（STAGE_H）", str(STAGE_H))
    return html


def main():
    if not ENGINE.exists():
        print(f"!! エンジンが見つかりません: {ENGINE}", file=sys.stderr)
        print("   tools/vendor/tuesday.js を用意してください(READMEの手順を参照)。", file=sys.stderr)
        sys.exit(1)

    with open(BASE / "game_complete.json", encoding="utf-8") as f:
        story = json.load(f)
    with open(ENGINE, encoding="utf-8") as f:
        engine_src = f.read()

    # --- index.html: 画像は相対パスのまま ---
    out1 = BASE / "index.html"
    with open(out1, "w", encoding="utf-8") as f:
        f.write(render(story, engine_src))
    print(f"index.html            : {out1.stat().st_size/1024/1024:6.2f} MB (画像は data/ 参照)")

    # --- game_standalone.html: 画像もbase64 ---
    paths = set()
    collect_image_paths(story, paths)
    base_arr = []
    index_map = {}
    total = 0
    for p in sorted(paths):
        full = BASE / p
        if not full.exists():
            print(f"  !! 見つかりません: {p}", file=sys.stderr)
            continue
        ext = os.path.splitext(p)[1].lower()
        mime = MIME.get(ext)
        if not mime:
            print(f"  !! 未知の拡張子: {p}", file=sys.stderr)
            continue
        with open(full, "rb") as fh:
            base_arr.append(f"data:{mime};base64," + base64.b64encode(fh.read()).decode("ascii"))
        index_map[p] = len(base_arr)  # art_data() は 1-based
        total += full.stat().st_size
    print(f"  埋め込んだ画像: {len(base_arr)} 件 / {total/1024/1024:.1f} MB (重複排除済み)")

    story2 = inline_images(story, index_map)
    assert "base" not in story2, "base キーが既に使われている"
    story2["base"] = base_arr
    out2 = BASE / "game_standalone.html"
    with open(out2, "w", encoding="utf-8") as f:
        f.write(render(story2, engine_src))
    print(f"game_standalone.html  : {out2.stat().st_size/1024/1024:6.2f} MB (完全1ファイル)")


if __name__ == "__main__":
    main()
