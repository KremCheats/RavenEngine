#import "Aimbot.h"
#import "GameData.h"
#import "IL2CPP.h"
#import "Settings.h"
#import <UIKit/UIKit.h>
#include <cmath>
#include <cfloat>
#include <cstring>
#include <dlfcn.h>

namespace RavenAimbot {

static void* g_playerRootClass     = nullptr;
static void* g_playerMobViewClass  = nullptr;
static void* g_getTeamId           = nullptr;
static void* g_getActiveMobView    = nullptr;
static void* g_getMainCamera       = nullptr;
static void* g_getHeadTransform    = nullptr;
static void* g_getChestTransform   = nullptr;
static void* g_getPosition         = nullptr;
static void* g_transformClass      = nullptr;
static void* g_cameraCtrlClass     = nullptr;
static void* g_getRenderCamera     = nullptr;
static void* g_cameraClass         = nullptr;
static void* g_worldToScreen       = nullptr;
static bool  g_worldToScreenTwoArg = false;
static void* g_getRootTransform    = nullptr;
static void* g_displayRotationClass = nullptr;
static void* g_rotationDelta        = nullptr;
static void* g_updateRotationDelta  = nullptr;
static bool  g_resolved            = false;
static void* g_lockedTarget        = nullptr;
static double g_lockedSince        = 0.0;

static inline bool ptrOk(void* p) {
    uintptr_t v = (uintptr_t)p;
    return v >= 0x100000000ULL && v <= 0x8000000000ULL;
}

static void* resolveInherited(void* cls, const char* name, int argc) {
    for (void* c = cls; c; c = IL2CPP::classGetParent(c)) {
        void* m = IL2CPP::resolveMethod(c, name, argc);
        if (m) return m;
    }
    return nullptr;
}

static void resolveHandles(void) {
    if (g_resolved) return;
    void* img = IL2CPP::gameImage();
    if (!img) return;

    g_playerRootClass   = IL2CPP::klass(GameData::kNsPlayer,     GameData::kPlayerRootClass);
    g_playerMobViewClass= IL2CPP::klass(GameData::kNsPlayer,     GameData::kPlayerMobClass);
    g_cameraCtrlClass   = IL2CPP::klass(GameData::kNsCameraCtrl, GameData::kCameraCtrlClass);

    if (g_playerRootClass) {
        g_getTeamId        = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetTeamId, 0);
        g_getActiveMobView = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetActiveMobView, 0);
        g_getMainCamera    = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetMainCamera, 0);
        g_getRootTransform = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetTransform, 0);
    }
    if (g_playerMobViewClass) {
        g_getHeadTransform  = IL2CPP::resolveMethod(g_playerMobViewClass, GameData::kMGetHeadTransform, 0);
        g_getChestTransform = IL2CPP::resolveMethod(g_playerMobViewClass, GameData::kMGetChestTransform, 0);
    }
    if (g_cameraCtrlClass) {
        g_getRenderCamera  = IL2CPP::resolveMethod(g_cameraCtrlClass, GameData::kMGetRenderCamera, 0);
    }
    g_displayRotationClass = IL2CPP::klass("CombatMaster.Battle.InputControllers", "DisplayRotationSensor");
    if (g_displayRotationClass) {
        g_rotationDelta       = IL2CPP::resolveMethod(g_displayRotationClass, "get_DegreesDelta", 0);
        g_updateRotationDelta = IL2CPP::resolveMethod(g_displayRotationClass, "get_UpdateDegreesDelta", 0);

        // --- method enumeration probe (temporary diagnostic) ---
        typedef void* (*t_iter)(void*, void**);
        typedef const char* (*t_mname)(void*);
        typedef uint32_t (*t_pcount)(void*);
        t_iter   il2cpp_class_get_methods      = (t_iter)dlsym(RTLD_DEFAULT, "il2cpp_class_get_methods");
        t_mname  il2cpp_method_get_name        = (t_mname)dlsym(RTLD_DEFAULT, "il2cpp_method_get_name");
        t_pcount il2cpp_method_get_param_count = (t_pcount)dlsym(RTLD_DEFAULT, "il2cpp_method_get_param_count");
        if (il2cpp_class_get_methods && il2cpp_method_get_name) {
            void* iter = nullptr;
            void* m = nullptr;
            int n = 0;
            while ((m = il2cpp_class_get_methods(g_displayRotationClass, &iter)) != nullptr && n < 200) {
                const char* name = il2cpp_method_get_name(m);
                int argc = il2cpp_method_get_param_count ? (int)il2cpp_method_get_param_count(m) : -1;
                RAVEN_LOG("rotmethod[%d]: %s argc=%d ptr=%p", n, name ? name : "(null)", argc, m);
                n++;
            }
            RAVEN_LOG("rotmethod: enumerated %d methods on DisplayRotationSensor", n);
        }
    }
    g_resolved = (g_playerRootClass && g_cameraCtrlClass && g_getTeamId &&
                  g_getActiveMobView && g_getRenderCamera);
}

static void ensureTransformClass(void* obj) {
    if (!obj || g_transformClass) return;
    g_transformClass = IL2CPP::objectGetClass(obj);
    if (g_transformClass) {
        g_getPosition = IL2CPP::resolveMethod(g_transformClass, GameData::kMGetPosition, 0);
    }
}

static void ensureCameraClass(void* obj) {
    if (!obj || g_cameraClass) return;
    g_cameraClass = IL2CPP::objectGetClass(obj);
    if (!g_cameraClass)
        g_cameraClass = IL2CPP::klass("UnityEngine", "Camera");
    if (g_cameraClass) {
        g_worldToScreen = IL2CPP::resolveMethod(g_cameraClass, GameData::kMWorldToScreen, 1);
        if (!g_worldToScreen) {
            g_worldToScreen = IL2CPP::resolveMethod(g_cameraClass, GameData::kMWorldToScreen, 2);
            g_worldToScreenTwoArg = (g_worldToScreen != nullptr);
        }
    }
}

static inline int32_t readInt32(void* o, uint32_t off) { return o ? *(int32_t*)((uint8_t*)o+off) : 0; }
static inline void*   readPtr(void* o, uint32_t off)   { return o ? *(void**)((uint8_t*)o+off) : nullptr; }

static void* invokePtr(void* method, void* obj) {
    if (!method || !obj) return nullptr;
    return IL2CPP::invokeMethod(method, obj, nullptr);
}
static int32_t invokeInt(void* method, void* obj) {
    if (!method || !obj) return 0;
    void* r = IL2CPP::invokeMethod(method, obj, nullptr);
    return r ? *(int32_t*)((uint8_t*)r + 0x10) : 0;
}

static bool readTransformPos(void* t, Vec3* out) {
    if (!t) return false;
    ensureTransformClass(t);
    if (!g_getPosition) return false;
    void* r = IL2CPP::invokeMethod(g_getPosition, t, nullptr);
    if (!r) return false;
    *out = *(Vec3*)((uint8_t*)r + 0x10);
    return true;
}

static bool worldToScreen(void* cam, Vec3 w, CGSize scr, CGPoint* out) {
    if (!cam) return false;
    ensureCameraClass(cam);
    if (!g_worldToScreen) return false;
    Vec3 arg = w;
    int monoEye = 0;
    void* oneArg[1] = { &arg };
    void* twoArgs[2] = { &arg, &monoEye };
    void** args = g_worldToScreenTwoArg ? twoArgs : oneArg;
    void* r = IL2CPP::invokeMethod(g_worldToScreen, cam, args);
    if (!r) return false;
    Vec3 sp = *(Vec3*)((uint8_t*)r + 0x10);
    if (sp.z < 0.01f) return false;
    if (!(sp.x == sp.x) || !(sp.y == sp.y) || !(sp.z == sp.z)) return false;
    if (fabsf(sp.x) > 1.0e6f || fabsf(sp.y) > 1.0e6f) return false;
    CGSize native = [UIScreen mainScreen].nativeBounds.size;
    CGFloat nativeW = MAX(native.width, native.height);
    CGFloat nativeH = MIN(native.width, native.height);
    if (nativeW < 1.0 || nativeH < 1.0) {
        CGFloat scale = MAX(1.0, [UIScreen mainScreen].scale);
        nativeW = scr.width * scale;
        nativeH = scr.height * scale;
    }
    out->x = (sp.x / nativeW) * scr.width;
    out->y = scr.height - ((sp.y / nativeH) * scr.height);
    return (out->x >= -100 && out->x <= scr.width + 100 &&
            out->y >= -100 && out->y <= scr.height + 100);
}

struct FrozenDetector {
    float lastX = 0.0f, lastY = 0.0f, lastZ = 0.0f;
    int   identicalCount = 0;
    bool  warned = false;
    void* boundTo = nullptr;

    void reset(void* local) {
        lastX = lastY = lastZ = 0.0f;
        identicalCount = 0;
        warned = false;
        boundTo = local;
    }
    bool observe(void* local, Vec3 v) {
        if (local != boundTo) reset(local);
        bool same = (v.x == lastX && v.y == lastY && v.z == lastZ);
        lastX = v.x; lastY = v.y; lastZ = v.z;
        if (same) { if (identicalCount < 1000000) identicalCount++; }
        else { identicalCount = 0; }
        if (identicalCount >= 60 && !warned) {
            warned = true;
            RAVEN_LOG("aim-frozen: root transform stale for %d ticks", identicalCount);
        }
        return !warned;
    }
};

static void* findBestTarget(void* localPlayer, int localTeam, void* camera, Vec3* outAimPoint) {
    void* list = IL2CPP::readStaticFieldObject(g_playerRootClass, GameData::kFldAllPlayers);
    if (!ptrOk(list)) return nullptr;

    void* itemsArray = readPtr(list, GameData::List::Items);
    int   count      = readInt32(list, GameData::List::Size);
    if (!ptrOk(itemsArray) || count <= 0) return nullptr;
    void** items = (void**)((uint8_t*)itemsArray + GameData::Array::Data);

    CGSize scr = [UIScreen mainScreen].bounds.size;
    CGPoint center = CGPointMake(scr.width / 2.0, scr.height / 2.0);
    float fovPx = (RavenSettings::aimFov / 90.0f) * (scr.width / 2.0f);

    if (g_lockedTarget) {
        bool stillPresent = false;
        for (int i = 0; i < count; i++) {
            if (items[i] == g_lockedTarget) { stillPresent = true; break; }
        }
        if (!stillPresent) {
            g_lockedTarget = nullptr;
            g_lockedSince = 0.0;
        }
    }

    void* best = nullptr;
    float bestDist = FLT_MAX;
    Vec3 bestAim = {0,0,0};
    Vec3 lockedAim = {0,0,0};
    bool lockedVisible = false;
    Vec3 localPos = {0,0,0};
    void* localTransform = g_getRootTransform ? invokePtr(g_getRootTransform, localPlayer) : nullptr;
    if (ptrOk(localTransform)) readTransformPos(localTransform, &localPos);

    for (int i = 0; i < count; i++) {
        void* p = items[i];
        if (!p || p == localPlayer) continue;
        if (!ptrOk(p)) continue;
        int team = g_getTeamId ? invokeInt(g_getTeamId, p) : 0;
        if (team != 0 && team == localTeam) continue;

        void* targetTransform = g_getRootTransform ? invokePtr(g_getRootTransform, p) : nullptr;
        Vec3 targetPos = {0,0,0};
        if (!ptrOk(targetTransform) || !readTransformPos(targetTransform, &targetPos)) continue;

        Vec3 bonePos = targetPos;
        void* mobView = g_getActiveMobView ? invokePtr(g_getActiveMobView, p) : nullptr;
        if (!ptrOk(mobView)) mobView = nullptr;
        void* bone = nullptr;
        if (mobView) {
            if (RavenSettings::aimBone == 0) {
                bone = g_getHeadTransform ? invokePtr(g_getHeadTransform, mobView) : nullptr;
            } else {
                bone = g_getChestTransform ? invokePtr(g_getChestTransform, mobView) : nullptr;
            }
        }
        if (!ptrOk(bone) || !readTransformPos(bone, &bonePos)) {
            bonePos.y += (RavenSettings::aimBone == 0) ? 1.65f : 1.15f;
        }
        Vec3 delta = {targetPos.x - localPos.x, targetPos.y - localPos.y, targetPos.z - localPos.z};
        float worldDistance = sqrtf(delta.x*delta.x + delta.y*delta.y + delta.z*delta.z);
        if (RavenSettings::aimMaxDist > 0.0f && worldDistance > RavenSettings::aimMaxDist) continue;

        CGPoint screen;
        if (!worldToScreen(camera, bonePos, scr, &screen)) continue;

        float d = hypotf(screen.x - center.x, screen.y - center.y);
        if (d > fovPx) continue;
        if (p == g_lockedTarget) { lockedAim = bonePos; lockedVisible = true; }
        if (d < bestDist) { bestDist = d; best = p; bestAim = bonePos; }
    }

    double now = CACurrentMediaTime();
    double switchDelay = MAX(0.0, (double)RavenSettings::aimSwitchDelay) / 1000.0;
    if (g_lockedTarget && lockedVisible && switchDelay > 0.0 &&
        (now - g_lockedSince) < switchDelay) {
        *outAimPoint = lockedAim;
        return g_lockedTarget;
    }
    if (best) {
        if (best != g_lockedTarget) {
            g_lockedTarget = best;
            g_lockedSince = now;
        }
        *outAimPoint = bestAim;
    } else if (!lockedVisible) {
        g_lockedTarget = nullptr;
    }
    return best;
}

void setEnabled(bool on) {
    RavenSettings::aimEnabled = on;
    if (!on) { g_lockedTarget = nullptr; g_lockedSince = 0.0; }
}

void tick() {
    if (!RavenSettings::aimEnabled) return;
    resolveHandles();
    if (!g_playerRootClass) return;

    void* localPlayer = IL2CPP::readStaticFieldObject(g_playerRootClass, GameData::kFldMyPlayer);
    if (!ptrOk(localPlayer)) return;

    int localTeam = g_getTeamId ? invokeInt(g_getTeamId, localPlayer) : 0;

    void* camera = nullptr;
    {
        void* camCtrl = readPtr(localPlayer, GameData::PlayerRoot::CameraController);
        if (ptrOk(camCtrl) && g_getRenderCamera)
            camera = invokePtr(g_getRenderCamera, camCtrl);
    }
    if (!ptrOk(camera) && g_getMainCamera)
        camera = invokePtr(g_getMainCamera, localPlayer);
    if (!ptrOk(camera)) return;

    // ---- Local eye position ----
    void* localT = g_getRootTransform ? invokePtr(g_getRootTransform, localPlayer) : nullptr;
    Vec3 srcA = {0,0,0};
    bool haveA = ptrOk(localT) && readTransformPos(localT, &srcA);

    static void* s_camGetTransform = nullptr;
    if (!s_camGetTransform) {
        ensureCameraClass(camera);
        if (g_cameraClass)
            s_camGetTransform = resolveInherited(g_cameraClass, GameData::kMGetTransform, 0);
    }
    void* camT = s_camGetTransform ? invokePtr(s_camGetTransform, camera) : nullptr;
    Vec3 srcB = {0,0,0};
    bool haveB = ptrOk(camT) && readTransformPos(camT, &srcB);

    static FrozenDetector s_frozen;
    Vec3 src = {0,0,0};
    bool usingCamera = false;
    if (haveA) {
        bool liveA = s_frozen.observe(localPlayer, srcA);
        if (liveA) { src = srcA; }
        else if (haveB) { src = srcB; usingCamera = true; }
        else return;
    } else if (haveB) { src = srcB; usingCamera = true; }
    else return;
    if (!usingCamera) src.y += 1.65f;

    // ---- Target ----
    Vec3 aimPoint = {0,0,0};
    void* target = findBestTarget(localPlayer, localTeam, camera, &aimPoint);
    if (!target) return;

    // ---- Screen-space delta ----
    CGSize scr = [UIScreen mainScreen].bounds.size;
    CGPoint screen;
    if (!worldToScreen(camera, aimPoint, scr, &screen)) return;

    float dx_px = screen.x - scr.width * 0.5f;
    float dy_px = screen.y - scr.height * 0.5f;

    float fov = MAX(10.0f, RavenSettings::aimFov);
    float halfFovDeg = fov * 0.5f;
    float degPerPxX = halfFovDeg / (scr.width * 0.5f);
    float degPerPxY = halfFovDeg / (scr.height * 0.5f);

    float d_yaw   = dx_px * degPerPxX;
    float d_pitch = -dy_px * degPerPxY;

    float smooth = MAX(1.0f, RavenSettings::aimSmooth);
    d_yaw   *= (1.0f / smooth);
    d_pitch *= (1.0f / smooth);

    float maxDeg = 20.0f;
    d_yaw   = MAX(-maxDeg, MIN(maxDeg, d_yaw));
    d_pitch = MAX(-maxDeg, MIN(maxDeg, d_pitch));

    // ---- Write delta to sensor field ----
    //
    // Delta the camera consumes lives at sensor+0x38 (confirmed against
    // get_DegreesDelta()). Prior versions wrote to +0x28 (scratch) or
    // mirrored to +0x40 (unrelated pipeline — caused snap-up). Both removed.
    //
    // We add onto whatever is already there so we blend with touch input
    // rather than replace it.
    void* inputController = readPtr(localPlayer, 0xE8);
    void* rotationSensor = ptrOk(inputController) ? readPtr(inputController, 0x168) : nullptr;

    bool applied = false;
    float pre38y = 0, pre38p = 0, post38y = 0, post38p = 0;
    if (ptrOk(rotationSensor)) {
        uint8_t* p = (uint8_t*)rotationSensor;
        pre38y = *(float*)(p + 0x38);
        pre38p = *(float*)(p + 0x3C);
        if (isfinite(pre38y) && isfinite(pre38p) &&
            fabsf(pre38y) < 720.f && fabsf(pre38p) < 720.f) {
            *(float*)(p + 0x38) = pre38y + d_yaw;
            *(float*)(p + 0x3C) = pre38p + d_pitch;
            post38y = *(float*)(p + 0x38);
            post38p = *(float*)(p + 0x3C);
            applied = true;
        }
    }

    static int applyLogCount = 0;
    if (applyLogCount < 120) {
        RAVEN_LOG("aim-apply: d=(%.2f,%.2f) applied=%d sensor=%p pre=(%.3f,%.3f) post=(%.3f,%.3f)",
                  d_yaw, d_pitch, applied, rotationSensor, pre38y, pre38p, post38y, post38p);
        applyLogCount++;
    }
}

} // namespace RavenAimbot
