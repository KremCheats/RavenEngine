// Root cause fix
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
static void* g_playerHealthClass   = nullptr;
static void* g_playerMobViewClass  = nullptr;
static void* g_getTeamId           = nullptr;
static void* g_getActiveMobView    = nullptr;
static void* g_getIsVisible        = nullptr;
static void* g_getIsDead           = nullptr;
static void* g_getIsDowned         = nullptr;
static void* g_getMainCamera       = nullptr;
static void* g_getHeadTransform    = nullptr;
static void* g_getNeckTransform    = nullptr;
static void* g_getChestTransform   = nullptr;
static void* g_getPelvisTransform  = nullptr;
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
static void* g_clearRotationDelta   = nullptr;
static bool  g_resolved            = false;

// ---- lock state -------------------------------------------------
static void*  g_lockedTarget      = nullptr;
static double g_lockedSince       = 0.0;
static int    g_lockTicks         = 0;
static float  g_lockedScreenD     = FLT_MAX;
static float  g_lockedScore       = FLT_MAX;

// ---- write bounds ----------------------------------------------
static const float AIM_MAX_YAW_STEP   =   8.0f;
static const float AIM_MAX_PITCH_STEP =  6.0f;
static const int   AIM_LOCK_MIN_TICKS =  10;
static const float AIM_SWITCH_HYST_PX =  60.0f;
static const float AIM_DEADZONE_PX    =   0.75f;

// ---- ClearDegreesDelta hook ------------------------------------
//
// Earlier build hooked get_DegreesDelta. That hook installed clean
// but never fired — the getter is inlined at IL2CPP translation
// time and the game never calls through the MethodInfo's method
// pointer. So the hook was dead code.
//
// ClearDegreesDelta is called by the game's own update pipeline at
// the end of every frame, after it has read and consumed the delta.
// We hook it, let the original clear the field, then write our
// pending delta. The next frame's read sees our value. Single-order
// write, no race, no timing window.
typedef void (*t_ClearDegreesDelta)(void* self, void* methodInfo);
static t_ClearDegreesDelta g_orig_ClearDegreesDelta = nullptr;
static void*  g_hookedSensor     = nullptr;
static void*  g_pendingSensor    = nullptr;
static float  g_pendingYaw       = 0.0f;
static float  g_pendingPitch     = 0.0f;
static bool   g_pendingFresh     = false;
static int    g_hookFireCount    = 0;

extern "C" void hook_ClearDegreesDelta(void* self, void* methodInfo) {
    if (g_orig_ClearDegreesDelta) g_orig_ClearDegreesDelta(self, methodInfo);

    // A sensor can be replaced during respawn or camera transitions. Never
    // apply a delta calculated for a previous sensor to the new object.
    if (g_pendingFresh && self == g_pendingSensor && self == g_hookedSensor) {
        uint8_t* p = (uint8_t*)self;
        *(float*)(p + 0x38) = g_pendingYaw;
        *(float*)(p + 0x3C) = g_pendingPitch;
        g_pendingFresh = false;

        if (g_hookFireCount < 40) {
            g_hookFireCount++;
            RAVEN_LOG("aim-hook: ClearDegreesDelta fired n=%d self=%p wrote=(%.3f,%.3f)",
                      g_hookFireCount, self, g_pendingYaw, g_pendingPitch);
        }
    } else if (self != g_pendingSensor) {
        g_pendingFresh = false;
    }
}

static inline bool ptrOk(void* p) {
    uintptr_t v = (uintptr_t)p;
    return v >= 0x100000000ULL && v <= 0x8000000000ULL;
}

static inline float clampf(float v, float lo, float hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

static void applyPrediction(void* target, Vec3 currentPos, Vec3* aimPoint) {
    static void* previousTarget = nullptr;
    static Vec3 previousPos = {0, 0, 0};
    static double previousTime = 0.0;
    double now = CACurrentMediaTime();
    double dt = now - previousTime;
    if (!RavenSettings::aimPrediction || !target || dt <= 0.0 || dt > 0.25 || target != previousTarget) {
        previousTarget = target;
        previousPos = currentPos;
        previousTime = now;
        return;
    }
    Vec3 velocity = {
        (currentPos.x - previousPos.x) / (float)dt,
        (currentPos.y - previousPos.y) / (float)dt,
        (currentPos.z - previousPos.z) / (float)dt,
    };
    float speed = sqrtf(velocity.x * velocity.x + velocity.y * velocity.y + velocity.z * velocity.z);
    if (isfinite(speed) && speed > 0.01f) {
        float cap = 35.0f;
        if (speed > cap) {
            float scale = cap / speed;
            velocity.x *= scale; velocity.y *= scale; velocity.z *= scale;
        }
        float lead = clampf(0.045f + speed * 0.0015f, 0.045f, 0.12f);
        aimPoint->x += velocity.x * lead;
        aimPoint->y += velocity.y * lead;
        aimPoint->z += velocity.z * lead;
    }
    previousTarget = target;
    previousPos = currentPos;
    previousTime = now;
}

static float smoothingMultiplier(float smooth, int curve) {
    float base = 1.0f / MAX(1.0f, smooth);
    switch (curve) {
        case 0: return base;                         // linear
        case 2: return 1.0f - powf(1.0f - base, 2.0f); // ease-out
        case 3: return 1.0f;                         // instant
        default: return powf(base, 0.72f);           // exponential
    }
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
    g_playerHealthClass = IL2CPP::klass(GameData::kNsPlayer,     GameData::kPlayerHealthClass);
    g_playerMobViewClass= IL2CPP::klass(GameData::kNsPlayer,     GameData::kPlayerMobClass);
    g_cameraCtrlClass   = IL2CPP::klass(GameData::kNsCameraCtrl, GameData::kCameraCtrlClass);

    if (g_playerRootClass) {
        g_getTeamId        = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetTeamId, 0);
        g_getActiveMobView = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetActiveMobView, 0);
        g_getIsVisible     = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetIsVisible, 0);
        g_getMainCamera    = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetMainCamera, 0);
        g_getRootTransform = IL2CPP::resolveMethod(g_playerRootClass, GameData::kMGetTransform, 0);
    }
    if (g_playerHealthClass) {
        g_getIsDead   = IL2CPP::resolveMethod(g_playerHealthClass, GameData::kMGetIsDead, 0);
        g_getIsDowned = IL2CPP::resolveMethod(g_playerHealthClass, GameData::kMGetIsDowned, 0);
    }
    if (g_playerMobViewClass) {
        g_getHeadTransform  = IL2CPP::resolveMethod(g_playerMobViewClass, GameData::kMGetHeadTransform, 0);
        g_getNeckTransform  = IL2CPP::resolveMethod(g_playerMobViewClass, GameData::kMGetNeckTransform, 0);
        g_getChestTransform = IL2CPP::resolveMethod(g_playerMobViewClass, GameData::kMGetChestTransform, 0);
        g_getPelvisTransform= IL2CPP::resolveMethod(g_playerMobViewClass, GameData::kMGetPelvisTransform, 0);
    }
    if (g_cameraCtrlClass) {
        g_getRenderCamera  = IL2CPP::resolveMethod(g_cameraCtrlClass, GameData::kMGetRenderCamera, 0);
    }

    g_displayRotationClass = IL2CPP::klass("CombatMaster.Battle.InputControllers", "DisplayRotationSensor");
    if (g_displayRotationClass) {
        g_rotationDelta       = IL2CPP::resolveMethod(g_displayRotationClass, "get_DegreesDelta", 0);
        g_updateRotationDelta = IL2CPP::resolveMethod(g_displayRotationClass, "get_UpdateDegreesDelta", 0);
        g_clearRotationDelta  = IL2CPP::resolveMethod(g_displayRotationClass, "ClearDegreesDelta", 0);

        if (g_clearRotationDelta) {
            void* f0 = *(void**)((uint8_t*)g_clearRotationDelta + 0x00);
            RAVEN_LOG("aim-hook: ClearDegreesDelta MethodInfo=%p pointer=%p", g_clearRotationDelta, f0);
            if (ptrOk(f0)) {
                g_orig_ClearDegreesDelta = (t_ClearDegreesDelta)f0;
                *(void**)((uint8_t*)g_clearRotationDelta + 0x00) = (void*)hook_ClearDegreesDelta;
                RAVEN_LOG("aim-hook: installed ClearDegreesDelta hook, orig=%p", g_orig_ClearDegreesDelta);
            } else {
                RAVEN_LOG("aim-hook: ClearDegreesDelta pointer invalid (%p), hook skipped", f0);
            }
        } else {
            RAVEN_LOG("aim-hook: ClearDegreesDelta not resolved");
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
static bool invokeBool(void* method, void* obj) {
    if (!method || !obj) return false;
    void* r = IL2CPP::invokeMethod(method, obj, nullptr);
    return r ? *(bool*)((uint8_t*)r + 0x10) : false;
}

static inline uint8_t readU8(void* obj, uint32_t off) {
    return obj ? *(uint8_t*)((uint8_t*)obj + off) : 0;
}

static bool targetIsAlive(void* player) {
    if (!ptrOk(player)) return false;
    void* health = readPtr(player, GameData::PlayerRoot::PlayerHealth);
    if (ptrOk(health)) {
        if (g_getIsDead && invokeBool(g_getIsDead, health)) return false;
        if (g_getIsDowned && invokeBool(g_getIsDowned, health)) return false;
    }
    // IsRealPlayer is still marked unverified in GameData.h. Read it only for
    // diagnostics; using it as a hard gate would recreate the phantom-target
    // bug if the offset is wrong on a different build.
    return true;
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
    float fovPx = (MAX(1.0f, RavenSettings::aimFov) / 90.0f) * (scr.width / 2.0f);

    if (g_lockedTarget && !targetIsAlive(g_lockedTarget)) {
        g_lockedTarget = nullptr;
        g_lockedSince = 0.0;
        g_lockTicks = 0;
        g_lockedScreenD = FLT_MAX;
        g_lockedScore = FLT_MAX;
    } else if (g_lockedTarget) {
        bool stillPresent = false;
        for (int i = 0; i < count; i++) {
            if (items[i] == g_lockedTarget) { stillPresent = true; break; }
        }
        if (!stillPresent) {
            g_lockedTarget = nullptr;
            g_lockedSince = 0.0;
            g_lockTicks = 0;
            g_lockedScreenD = FLT_MAX;
            g_lockedScore = FLT_MAX;
        }
    }

    void* best = nullptr;
    float bestDist = FLT_MAX;
    float bestScore = FLT_MAX;
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
        if (!targetIsAlive(p)) continue;
        int team = g_getTeamId ? invokeInt(g_getTeamId, p) : 0;
        if (team != 0 && team == localTeam) continue;
        if (RavenSettings::aimVisCheck && g_getIsVisible && !invokeBool(g_getIsVisible, p)) continue;

        void* targetTransform = g_getRootTransform ? invokePtr(g_getRootTransform, p) : nullptr;
        Vec3 targetPos = {0,0,0};
        if (!ptrOk(targetTransform) || !readTransformPos(targetTransform, &targetPos)) continue;

        Vec3 bonePos = targetPos;
        void* mobView = g_getActiveMobView ? invokePtr(g_getActiveMobView, p) : nullptr;
        if (!ptrOk(mobView)) mobView = nullptr;
        void* bone = nullptr;
        if (mobView) {
            if (RavenSettings::aimBone == 0)
                bone = g_getHeadTransform ? invokePtr(g_getHeadTransform, mobView) : nullptr;
            else if (RavenSettings::aimBone == 1)
                bone = g_getNeckTransform ? invokePtr(g_getNeckTransform, mobView) : nullptr;
            else if (RavenSettings::aimBone == 2)
                bone = g_getChestTransform ? invokePtr(g_getChestTransform, mobView) : nullptr;
            else
                bone = g_getPelvisTransform ? invokePtr(g_getPelvisTransform, mobView) : nullptr;
        }
        if (!ptrOk(bone) || !readTransformPos(bone, &bonePos)) {
            static const float fallbackHeight[] = { 1.65f, 1.42f, 1.15f, 0.85f };
            int boneIndex = MAX(0, MIN(3, RavenSettings::aimBone));
            bonePos.y += fallbackHeight[boneIndex];
        }
        Vec3 delta = {targetPos.x - localPos.x, targetPos.y - localPos.y, targetPos.z - localPos.z};
        float worldDistance = sqrtf(delta.x*delta.x + delta.y*delta.y + delta.z*delta.z);
        if (RavenSettings::aimMaxDist > 0.0f && worldDistance > RavenSettings::aimMaxDist) continue;

        CGPoint screen;
        if (!worldToScreen(camera, bonePos, scr, &screen)) continue;

        float d = hypotf(screen.x - center.x, screen.y - center.y);
        if (d > fovPx || d < AIM_DEADZONE_PX && p == g_lockedTarget) continue;
        if (p == g_lockedTarget) { lockedAim = bonePos; lockedVisible = true; g_lockedScreenD = d; }
        float score = d;
        if (RavenSettings::aimPriority == 1) score = worldDistance;
        else if (RavenSettings::aimPriority == 2) score = d + worldDistance * 0.35f;
        else if (RavenSettings::aimPriority >= 3) score = worldDistance + d * 0.05f;
        if (score < bestScore) {
            bestScore = score;
            bestDist = d;
            best = p;
            bestAim = bonePos;
        }
    }

    double now = CACurrentMediaTime();
    double switchDelay = MAX(0.0, (double)RavenSettings::aimSwitchDelay) / 1000.0;

    if (g_lockedTarget && lockedVisible && switchDelay > 0.0 &&
        (now - g_lockedSince) < switchDelay) {
        *outAimPoint = lockedAim;
        applyPrediction(g_lockedTarget, lockedAim, outAimPoint);
        g_lockTicks++;
        return g_lockedTarget;
    }

    if (g_lockedTarget && lockedVisible && g_lockTicks < AIM_LOCK_MIN_TICKS) {
        *outAimPoint = lockedAim;
        applyPrediction(g_lockedTarget, lockedAim, outAimPoint);
        g_lockTicks++;
        return g_lockedTarget;
    }

    if (best) {
        if (best == g_lockedTarget) {
            g_lockedScreenD = bestDist;
            g_lockedScore = bestScore;
            g_lockTicks++;
        } else {
            bool canSwitch = (g_lockedTarget == nullptr)
                           || (bestScore + AIM_SWITCH_HYST_PX < g_lockedScore);
            if (canSwitch) {
                g_lockedTarget  = best;
                g_lockedSince   = now;
                g_lockTicks     = 0;
                g_lockedScreenD = bestDist;
                g_lockedScore   = bestScore;
            } else {
                if (lockedVisible) {
                    *outAimPoint = lockedAim;
                    applyPrediction(g_lockedTarget, lockedAim, outAimPoint);
                    g_lockTicks++;
                    return g_lockedTarget;
                }
            }
        }
        *outAimPoint = bestAim;
        applyPrediction(best, bestAim, outAimPoint);
    } else if (!lockedVisible) {
        g_lockedTarget = nullptr;
        g_lockTicks = 0;
        g_lockedScreenD = FLT_MAX;
        g_lockedScore = FLT_MAX;
    }
    return best;
}

void setEnabled(bool on) {
    RavenSettings::aimEnabled = on;
    if (!on) {
        g_lockedTarget = nullptr;
        g_lockedSince = 0.0;
        g_lockTicks = 0;
        g_lockedScreenD = FLT_MAX;
        g_lockedScore = FLT_MAX;
        g_pendingFresh = false;
        g_pendingYaw = 0.0f;
        g_pendingPitch = 0.0f;
        g_hookedSensor = nullptr;
        g_pendingSensor = nullptr;
    }
}

void tick() {
    if (!RavenSettings::aimEnabled) return;
    resolveHandles();

    static double s_aimSigLast = 0.0;
    double sigNow = CACurrentMediaTime();
    if (sigNow - s_aimSigLast >= 1.0) {
        s_aimSigLast = sigNow;
        RAVEN_LOG("aim: pc=%p cam=%p team=%p tf=%p",
                  g_playerRootClass, g_getMainCamera, g_getTeamId, g_getRootTransform);
    }

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

    Vec3 aimPoint = {0,0,0};
    void* target = findBestTarget(localPlayer, localTeam, camera, &aimPoint);
    if (!target) return;

    static double s_lastAimWrite = 0.0;
    double aimNow = CACurrentMediaTime();
    double aimDelay = MAX(0.0, (double)RavenSettings::aimDelay) / 1000.0;
    if (aimDelay > 0.0 && aimNow - s_lastAimWrite < aimDelay) return;

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
    float curve = smoothingMultiplier(smooth, RavenSettings::aimCurve);
    d_yaw   *= curve;
    d_pitch *= curve;

    d_yaw   = clampf(d_yaw,   -AIM_MAX_YAW_STEP,   AIM_MAX_YAW_STEP);
    d_pitch = clampf(d_pitch, -AIM_MAX_PITCH_STEP, AIM_MAX_PITCH_STEP);

    void* inputController = readPtr(localPlayer, 0xE8);
    void* rotationSensor = ptrOk(inputController) ? readPtr(inputController, 0x168) : nullptr;

    if (ptrOk(rotationSensor) && isfinite(d_yaw) && isfinite(d_pitch)) {
        g_pendingYaw   = d_yaw;
        g_pendingPitch = d_pitch;
        g_pendingFresh = true;
        g_hookedSensor = rotationSensor;
        g_pendingSensor = rotationSensor;
        s_lastAimWrite = aimNow;
    } else {
        g_pendingFresh = false;
    }

    static int applyLogCount = 0;
    if (applyLogCount < 60) {
        RAVEN_LOG("aim-apply: d=(%.2f,%.2f) sensor=%p hooked=%d pending=%d",
                  d_yaw, d_pitch, rotationSensor,
                  g_orig_ClearDegreesDelta != nullptr ? 1 : 0,
                  g_pendingFresh ? 1 : 0);
        applyLogCount++;
    }
}

} // namespace RavenAimbot
