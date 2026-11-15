#!/usr/bin/env python3
"""한사랑 마을 상태 점검. 실패하면 종료 코드 1.
확인: 라이브 페이지, 멀티 접속 키(길이·형식·역할·만료), 서버 응답, 직접 호스팅한 라이브러리, 3D 모델."""
import base64, json, re, sys, time, urllib.request, urllib.error
SITE = "https://rpsdl32-dotcom.github.io/hansarang-village/"
REF = "mdrrthfpdzjqrxfrojwf"
fails, notes = [], []
def get(url, headers=None, n=0):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "hsv-health"})
    with urllib.request.urlopen(req, timeout=25) as r: return r.status, (r.read() if n == 0 else r.read(n))
def check(name, ok, detail=""):
    (notes if ok else fails).append(("OK   " if ok else "FAIL ") + name + (" - " + detail if detail else "")); print(notes[-1] if ok else fails[-1])
try:
    st, body = get(SITE + "?hc=" + str(int(time.time()))); html = body.decode("utf-8", "replace")
    check("라이브 페이지 응답", st == 200 and "한사랑" in html, "HTTP %s, %d KB" % (st, len(html) // 1024))
except Exception as e:
    check("라이브 페이지 응답", False, repr(e)); html = ""
key = ""
m = re.search(r'key:\s*"(eyJ[A-Za-z0-9._-]*)"', html); key = m.group(1) if m else ""
check("접속 키가 들어 있음", bool(key))
check("접속 키 길이 정상(잘리지 않음)", len(key) >= 150, "%d자" % len(key))
if len(key) >= 150:
    try:
        pl = key.split(".")[1]; pl += "=" * (-len(pl) % 4); p = json.loads(base64.urlsafe_b64decode(pl))
        check("키 역할이 anon", p.get("role") == "anon", str(p.get("role")))
        check("키 프로젝트가 맞음", p.get("ref") == REF, str(p.get("ref")))
        days = (p.get("exp", 0) - time.time()) / 86400
        check("키 만료까지 30일 이상", days > 30, "%d일 남음" % days)
        try:
            st, _ = get("https://%s.supabase.co/auth/v1/settings" % REF, {"apikey": key, "User-Agent": "hsv-health"}, 200)
            check("멀티 서버 응답", st == 200, "HTTP %s" % st)
        except urllib.error.HTTPError as e: check("멀티 서버 응답", False, "HTTP %s" % e.code)
        except Exception as e: check("멀티 서버 응답", False, repr(e))
    except Exception as e: check("키 해석", False, repr(e))
for path in ["vendor/three/three.module.min.js", "vendor/three/examples/jsm/loaders/GLTFLoader.js", "vendor/three/examples/jsm/libs/draco/gltf/draco_decoder.wasm"]:
    try: st, _ = get(SITE + path, None, 64); check("파일 " + path, st == 200)
    except Exception as e: check("파일 " + path, False, repr(e))
models = ['apt.glb', 'ballret.glb', 'bowlfront.glb', 'cafedetail.glb', 'cafefront.glb', 'caferoof.glb', 'commerce.glb', 'cross.glb', 'entrance.glb', 'espresso.glb', 'floodhead.glb', 'goalnet.glb', 'harvest.glb', 'hatch.glb', 'kei.glb', 'magnolia.glb', 'mart.glb', 'pew.glb', 'piano.glb', 'pinset.glb', 'pulpit.glb', 'pylon.glb', 'race.glb', 'sedan.glb', 'sports.glb', 'stagechair.glb', 'standroof.glb', 'suv.glb', 'van.glb']  # 저장소의 *.glb 목록 (모델을 추가하면 이 목록도 갱신)
bad = 0
for mp in models:
    try: get(SITE + mp, None, 16)
    except Exception: bad += 1; print("  모델 없음:", mp)
check("3D 모델 파일 접근 (%d개)" % len(models), bad == 0 and len(models) > 0, "%d개 실패" % bad if bad else "")
print("\n결과: %d 통과 / %d 실패" % (len(notes), len(fails))); sys.exit(1 if fails else 0)
