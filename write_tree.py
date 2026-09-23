import os

def w(path, content):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        f.write(content.lstrip("\n"))

w("Makefile", r"""
TARGET = iphone:clang:latest:14.0
ARCHS = arm64

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = Raven
Raven_FILES = Raven.mm Src/IL2CPP.mm Src/ESP.mm Src/Aimbot.mm Src/Menu.mm Src/Updater.mm Src/Settings.mm
Raven_CFLAGS = -fobjc-arc -I./Src -std=c++17 -Wno-unused-function -Wno-deprecated-declarations
Raven_CCFLAGS = -fobjc-arc -I./Src -std=c++17
Raven_FRAMEWORKS = UIKit Foundation QuartzCore CoreGraphics

include $(THEOS_MAKE_PATH)/tweak.mk
""")

w("Raven.mm", r"""
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <dispatch/dispatch.h>
#import "Src/Common.h"
#import "Src/IL2CPP.h"
#import "Src/Menu.h"
#import "Src/Updater.h"
#import "Src/Logos.h"
#import "Src/Settings.h"

__attribute__((constructor))
static void raven_entry(void) {
    @autoreleasepool {
        RAVEN_LOG("entry");
        RavenSettings::load();
        Updater::fetchAsync(kConfigURL);
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(4 * NSEC_PER_SEC)),
                       dispatch_get_main_queue(), ^{
            IL2CPP::init();
            [[RavenMenu shared] start];
        });
    }
}
""")

w("Src/Common.h", r"""
#ifndef RAVEN_COMMON_H
#define RAVEN_COMMON_H

#include <cstdint>
#include <cstddef>

#import <Foundation/Foundation.h>
#import <os/log.h>

#define RAVEN_LOG(fmt, ...) os_log(OS_LOG_DEFAULT, "[raven] " fmt, ##__VA_ARGS__)

#define RAVEN_LOCAL_VERSION "1.0.0"

struct Vec3 { float x, y, z; };
struct Matrix4x4 { float m[16]; };

#define RAVEN_RED    [UIColor colorWithRed:0.835 green:0.122 blue:0.157 alpha:1.0]
#define RAVEN_SILVER [UIColor colorWithRed:0.949 green:0.949 blue:0.957 alpha:1.0]
#define RAVEN_GREY   [UIColor colorWithRed:0.573 green:0.573 blue:0.608 alpha:1.0]

#endif
""")

w("Src/GameData.h", r"""
#ifndef RAVEN_GAMEDATA_H
#define RAVEN_GAMEDATA_H

#include <cstdint>
#include "Updater.h"

namespace GameData {
    static const char* kLocalPlayerClass = "PlayerRoot";
    static const char* kPlayerListClass  = "PlayerManager";
    static const char* kCameraClass      = "Camera";
    static const char* kGameClass        = "GameManager";

    static const char* kGetInstance     = "get_Instance";
    static const char* kGetLocalPlayer  = "get_LocalPlayer";
    static const char* kGetAllPlayers   = "get_AllPlayers";
    static const char* kGetMainCamera   = "get_main";

    static const char* kFldHealth       = "Health";
    static const char* kFldArmor        = "Armor";
    static const char* kFldPosition     = "Position";
    static const char* kFldTeamId       = "TeamId";
    static const char* kFldIsVisible    = "IsVisible";
    static const char* kFldIsLocal      = "IsLocalPlayer";
    static const char* kFldName         = "PlayerName";

    static const char* kFldPlayerList   = "AllPlayers";

    namespace Off {
        inline uint32_t Health()     { return Updater::offset("Health", 0x0); }
        inline uint32_t Armor()      { return Updater::offset("Armor", 0x0); }
        inline uint32_t Position()   { return Updater::offset("Position", 0x0); }
        inline uint32_t TeamId()     { return Updater::offset("TeamId", 0x0); }
        inline uint32_t IsVisible()  { return Updater::offset("IsVisible", 0x0); }
        inline uint32_t IsLocal()    { return Updater::offset("IsLocal", 0x0); }
        inline uint32_t ListCount()  { return Updater::offset("ListCount", 0x18); }
        inline uint32_t ListItems()  { return Updater::offset("ListItems", 0x10); }
        inline uint32_t ArrayData()  { return Updater::offset("ArrayData", 0x20); }
        inline uint32_t ViewMatrix() { return Updater::offset("ViewMatrix", 0x0); }
        inline uint32_t ProjMatrix() { return Updater::offset("ProjMatrix", 0x0); }
    }

    namespace Bone {
        constexpr int Head   = 11;
        constexpr int Neck   = 12;
        constexpr int Chest  = 20;
        constexpr int Pelvis = 1;
    }
}

#endif
""")

w("Src/Logos.h", r"""
#ifndef RAVEN_LOGOS_H
#define RAVEN_LOGOS_H

static const char* kWordmarkURL  = "https://i.imgur.com/Cnzjdjh.png";
static const char* kBallLogoURL  = "https://i.imgur.com/MQG4stU.png";
static const char* kEmblemURL    = "https://i.imgur.com/vLJmsVo.png";

static const char* kConfigURL = "https://raw.githubusercontent.com/KremCheats/RuntimeSupport/main/config.json";

#endif
""")

w("Src/Settings.h", r"""
#ifndef RAVEN_SETTINGS_H
#define RAVEN_SETTINGS_H

namespace RavenSettings {
    void load();
    void save();

    extern bool  aimEnabled;
    extern int   aimBone;
    extern int   aimActivation;
    extern float aimFov;
    extern float aimSmooth;
    extern float aimMaxDist;
    extern bool  aimPrediction;
    extern bool  aimVisCheck;
    extern float aimDelay;
    extern float aimSwitchDelay;
    extern bool  aimShowCircle;
    extern float aimCircleRadius;
    extern float aimCircleThickness;

    extern bool  espEnabled;
    extern bool  espBox;
    extern bool  espCorner;
    extern bool  espSkeleton;
    extern bool  espSnaplines;
    extern bool  espName;
    extern bool  espDistance;
    extern bool  espHealth;
    extern bool  espWeapon;
    extern int   espEnemyColor;
    extern int   espVisibleColor;
    extern int   espSkeletonColor;
    extern int   espBoxColor;

    extern bool  visCrosshair;
    extern int   visCrosshairStyle;
    extern float visCrosshairSize;
    extern float visCrosshairThickness;
    extern bool  visFovCircle;
    extern float visFovRadius;
    extern float visFovThickness;
    extern bool  visRemoveFog;
    extern bool  visNightMode;
    extern bool  visBrightnessBoost;
    extern float visBrightness;
    extern bool  visNoFlash;
    extern bool  visNoSmoke;
    extern bool  visBetterTextures;

    extern bool  wpnNoRecoil;
    extern bool  wpnNoSpread;
    extern float wpnRecoilStrength;
    extern bool  wpnFastReload;
    extern bool  wpnRapidFire;
    extern float wpnFireRate;
    extern bool  wpnNoFlash;
    extern bool  wpnNoSmoke;
    extern bool  wpnNoShells;

    extern bool  miscBunnyHop;
    extern bool  miscAutoStrafe;
    extern bool  miscNoFallDamage;
    extern bool  miscUnlockAll;
    extern bool  miscNoAds;
    extern bool  miscPanicKey;
    extern bool  miscHideWhenClosed;
    extern float miscMenuOpacity;

    extern float menuScale;
    extern bool  animations;
}

#endif
""")

w("Src/Settings.mm", r"""
#import "Settings.h"
#import "Common.h"
#import <Foundation/Foundation.h>

namespace RavenSettings {

bool  aimEnabled = false;
int   aimBone = 0;
int   aimActivation = 0;
float aimFov = 120.0f;
float aimSmooth = 5.0f;
float aimMaxDist = 250.0f;
bool  aimPrediction = true;
bool  aimVisCheck = true;
float aimDelay = 0.0f;
float aimSwitchDelay = 120.0f;
bool  aimShowCircle = true;
float aimCircleRadius = 120.0f;
float aimCircleThickness = 2.0f;

bool  espEnabled = true;
bool  espBox = true;
bool  espCorner = false;
bool  espSkeleton = false;
bool  espSnaplines = false;
bool  espName = true;
bool  espDistance = true;
bool  espHealth = true;
bool  espWeapon = false;
int   espEnemyColor = 0;
int   espVisibleColor = 1;
int   espSkeletonColor = 2;
int   espBoxColor = 0;

bool  visCrosshair = true;
int   visCrosshairStyle = 0;
float visCrosshairSize = 6.0f;
float visCrosshairThickness = 2.0f;
bool  visFovCircle = false;
float visFovRadius = 120.0f;
float visFovThickness = 2.0f;
bool  visRemoveFog = true;
bool  visNightMode = true;
bool  visBrightnessBoost = true;
float visBrightness = 100.0f;
bool  visNoFlash = true;
bool  visNoSmoke = true;
bool  visBetterTextures = false;

bool  wpnNoRecoil = true;
bool  wpnNoSpread = true;
float wpnRecoilStrength = 0.0f;
bool  wpnFastReload = true;
bool  wpnRapidFire = true;
float wpnFireRate = 3.0f;
bool  wpnNoFlash = true;
bool  wpnNoSmoke = true;
bool  wpnNoShells = false;

bool  miscBunnyHop = true;
bool  miscAutoStrafe = true;
bool  miscNoFallDamage = false;
bool  miscUnlockAll = false;
bool  miscNoAds = false;
bool  miscPanicKey = true;
bool  miscHideWhenClosed = true;
float miscMenuOpacity = 97.0f;

float menuScale = 100.0f;
bool  animations = true;

static NSString* kKey(NSString* n) { return [@"raven." stringByAppendingString:n]; }

void load() {
    NSUserDefaults* d = [NSUserDefaults standardUserDefaults];
    aimEnabled = [d boolForKey:kKey(@"aim.enabled")];
    aimFov = [d floatForKey:kKey(@"aim.fov")];  if (aimFov <= 0) aimFov = 120;
    aimSmooth = [d floatForKey:kKey(@"aim.smooth")]; if (aimSmooth <= 0) aimSmooth = 5;
    espEnabled = [d objectForKey:kKey(@"esp.enabled")] ? [d boolForKey:kKey(@"esp.enabled")] : YES;
    miscMenuOpacity = [d floatForKey:kKey(@"misc.opacity")]; if (miscMenuOpacity <= 0) miscMenuOpacity = 97;
    menuScale = [d floatForKey:kKey(@"ui.scale")]; if (menuScale <= 0) menuScale = 100;
}

void save() {
    NSUserDefaults* d = [NSUserDefaults standardUserDefaults];
    [d setBool:aimEnabled forKey:kKey(@"aim.enabled")];
    [d setFloat:aimFov forKey:kKey(@"aim.fov")];
    [d setFloat:aimSmooth forKey:kKey(@"aim.smooth")];
    [d setBool:espEnabled forKey:kKey(@"esp.enabled")];
    [d setFloat:miscMenuOpacity forKey:kKey(@"misc.opacity")];
    [d setFloat:menuScale forKey:kKey(@"ui.scale")];
    [d synchronize];
}

}
""")

w("Src/Updater.h", r"""
#ifndef RAVEN_UPDATER_H
#define RAVEN_UPDATER_H

#include <cstdint>
#include <string>
#include <map>

namespace Updater {
    void fetchAsync(const char* url);
    std::string remoteVersion();
    bool hasUpdate();
    std::string updateMessage();
    uint32_t offset(const std::string& key, uint32_t fallback);
    bool feature(const std::string& key, bool fallback);
    std::string asset(const std::string& key, const std::string& fallback);
    const char* status();
}

#endif
""")

w("Src/Updater.mm", r"""
#import "Updater.h"
#import "Common.h"
#import <Foundation/Foundation.h>

namespace Updater {

static std::map<std::string,uint32_t> g_offsets;
static std::map<std::string,bool>     g_features;
static std::map<std::string,std::string> g_assets;
static std::string g_version    = RAVEN_LOCAL_VERSION;
static std::string g_minDylib   = RAVEN_LOCAL_VERSION;
static std::string g_message;
static bool g_fetched           = false;
static char g_status[160]       = "not fetched";

static uint32_t parseHex(const std::string& s) {
    if (s.empty()) return 0;
    return (uint32_t)strtoul(s.c_str(), nullptr, 16);
}

static std::string toStd(NSString* s) {
    if (!s) return std::string();
    return std::string([s UTF8String] ?: "");
}

static std::string cachePath() {
    NSString* d = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) firstObject];
    return toStd(d) + "/raven_config.json";
}

static bool parseConfig(NSData* data) {
    if (!data) return false;
    NSError* err = nil;
    id root = [NSJSONSerialization JSONObjectWithData:data options:0 error:&err];
    if (!root || ![root isKindOfClass:[NSDictionary class]]) return false;
    NSDictionary* d = (NSDictionary*)root;

    if (d[@"version"])           g_version  = toStd(d[@"version"]);
    if (d[@"min_dylib_version"]) g_minDylib = toStd(d[@"min_dylib_version"]);
    if (d[@"message"])           g_message  = toStd(d[@"message"]);

    g_offsets.clear();
    NSDictionary* offs = d[@"offsets"];
    if ([offs isKindOfClass:[NSDictionary class]])
        for (NSString* k in offs) g_offsets[toStd(k)] = parseHex(toStd(offs[k]));

    g_features.clear();
    NSDictionary* feats = d[@"features"];
    if ([feats isKindOfClass:[NSDictionary class]])
        for (NSString* k in feats) g_features[toStd(k)] = [feats[k] boolValue];

    g_assets.clear();
    NSDictionary* assets = d[@"assets"];
    if ([assets isKindOfClass:[NSDictionary class]])
        for (NSString* k in assets) g_assets[toStd(k)] = toStd(assets[k]);

    g_fetched = true;
    snprintf(g_status, sizeof(g_status), "config v%s (%zu offs)",
             g_version.c_str(), g_offsets.size());
    return true;
}

void fetchAsync(const char* url) {
    if (g_fetched) return;
    NSData* cached = [NSData dataWithContentsOfFile:
                      [NSString stringWithUTF8String:cachePath().c_str()]];
    if (cached && parseConfig(cached)) RAVEN_LOG("config loaded from cache");

    NSString* urlStr = [NSString stringWithUTF8String:url];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        NSURL* u = [NSURL URLWithString:urlStr];
        if (!u) return;
        NSData* fresh = [NSData dataWithContentsOfURL:u];
        if (!fresh) { RAVEN_LOG("config fetch failed"); return; }
        if (parseConfig(fresh)) {
            [fresh writeToFile:[NSString stringWithUTF8String:cachePath().c_str()]
                    atomically:YES];
            RAVEN_LOG("config refreshed: %s", g_status);
        }
    });
}

std::string remoteVersion() { return g_version; }
bool hasUpdate() { return g_fetched && g_version != std::string(RAVEN_LOCAL_VERSION); }
std::string updateMessage() { return g_message; }

uint32_t offset(const std::string& key, uint32_t fallback) {
    auto it = g_offsets.find(key);
    return it == g_offsets.end() ? fallback : it->second;
}
bool feature(const std::string& key, bool fallback) {
    auto it = g_features.find(key);
    return it == g_features.end() ? fallback : it->second;
}
std::string asset(const std::string& key, const std::string& fallback) {
    auto it = g_assets.find(key);
    return it == g_assets.end() ? fallback : it->second;
}
const char* status() { return g_status; }

}
""")

w("Src/IL2CPP.h", r"""
#ifndef RAVEN_IL2CPP_H
#define RAVEN_IL2CPP_H

#include <cstdint>
#include <string>
#include <vector>
#include "Common.h"

namespace IL2CPP {
    bool init();
    const char* status();

    void* domain();
    void* image(const char* assembly);
    void* klass(const char* ns, const char* name);
    void* method(void* klass, const char* name, int argc);
    void* field(void* klass, const char* name);

    void* invoke(void* method, void* obj, void** params);
    void* newObject(void* klass);

    template<typename T>
    inline T read(void* obj, uint32_t offset) {
        if (!obj) return T{};
        return *(T*)((uintptr_t)obj + offset);
    }

    template<typename T>
    inline void write(void* obj, uint32_t offset, T value) {
        if (!obj) return;
        *(T*)((uintptr_t)obj + offset) = value;
    }

    void* readListItems(void* obj, uint32_t itemsOffset);
    int   readListCount(void* obj, uint32_t countOffset);

    Matrix4x4 getViewProjection();
}
#endif
""")

w("Src/IL2CPP.mm", r"""
#import "IL2CPP.h"
#import "Common.h"
#import "GameData.h"
#import <dlfcn.h>
#import <cstdio>
#import <cstring>
#import <mach-o/dyld.h>
#import <mach-o/loader.h>

namespace IL2CPP {

typedef void*   (*t_domain_get)();
typedef void*   (*t_thread_attach)(void*);
typedef void*   (*t_domain_assembly_open)(void*, const char*);
typedef void*   (*t_assembly_get_image)(void*);
typedef void*   (*t_class_from_name)(void*, const char*, const char*);
typedef void*   (*t_class_get_method_from_name)(void*, const char*, int);
typedef void*   (*t_class_get_field_from_name)(void*, const char*);
typedef void*   (*t_runtime_invoke)(void*, void*, void**, void**);
typedef void*   (*t_object_new)(void*);
typedef uint32_t (*t_field_get_offset)(void*);

static t_domain_get p_domain_get = nullptr;
static t_thread_attach p_thread_attach = nullptr;
static t_domain_assembly_open p_domain_assembly_open = nullptr;
static t_assembly_get_image p_assembly_get_image = nullptr;
static t_class_from_name p_class_from_name = nullptr;
static t_class_get_method_from_name p_class_get_method_from_name = nullptr;
static t_class_get_field_from_name p_class_get_field_from_name = nullptr;
static t_runtime_invoke p_runtime_invoke = nullptr;
static t_object_new p_object_new = nullptr;
static t_field_get_offset p_field_get_offset = nullptr;

static void* g_domain = nullptr;
static void* g_img    = nullptr;
static char  g_status[200] = "not initialized";
static uintptr_t g_base = 0;

static void* rs(const char* n) { return dlsym(RTLD_DEFAULT, n); }

bool init() {
    uint32_t n = _dyld_image_count();
    for (uint32_t i = 0; i < n; i++) {
        const char* nm = _dyld_get_image_name(i);
        if (nm && (strstr(nm, "UnityFramework") || strstr(nm, "GameAssembly"))) {
            g_base = (uintptr_t)_dyld_get_image_header(i);
            break;
        }
    }
    if (!g_base && n > 0) g_base = (uintptr_t)_dyld_get_image_header(0);

    p_domain_get = (t_domain_get)rs("il2cpp_domain_get");
    p_thread_attach = (t_thread_attach)rs("il2cpp_thread_attach");
    p_domain_assembly_open = (t_domain_assembly_open)rs("il2cpp_domain_assembly_open");
    p_assembly_get_image = (t_assembly_get_image)rs("il2cpp_assembly_get_image");
    p_class_from_name = (t_class_from_name)rs("il2cpp_class_from_name");
    p_class_get_method_from_name = (t_class_get_method_from_name)rs("il2cpp_class_get_method_from_name");
    p_class_get_field_from_name = (t_class_get_field_from_name)rs("il2cpp_class_get_field_from_name");
    p_runtime_invoke = (t_runtime_invoke)rs("il2cpp_runtime_invoke");
    p_object_new = (t_object_new)rs("il2cpp_object_new");
    p_field_get_offset = (t_field_get_offset)rs("il2cpp_field_get_offset");

    if (!p_domain_get || !p_class_from_name || !p_assembly_get_image) {
        snprintf(g_status, sizeof(g_status), "il2cpp exports missing");
        return false;
    }
    g_domain = p_domain_get();
    if (!g_domain) { snprintf(g_status, sizeof(g_status), "null domain"); return false; }
    if (p_thread_attach) p_thread_attach(g_domain);
    snprintf(g_status, sizeof(g_status), "il2cpp ok");
    return true;
}

const char* status() { return g_status; }
void* domain() { return g_domain; }

void* image(const char* assembly) {
    if (!g_domain || !p_domain_assembly_open || !p_assembly_get_image) return nullptr;
    void* asm_ = p_domain_assembly_open(g_domain, assembly);
    if (!asm_) return nullptr;
    return p_assembly_get_image(asm_);
}

void* klass(const char* ns, const char* name) {
    if (!g_img) g_img = image("Assembly-CSharp");
    if (!g_img || !p_class_from_name) return nullptr;
    return p_class_from_name(g_img, ns, name);
}

void* method(void* k, const char* name, int argc) {
    if (!k || !p_class_get_method_from_name) return nullptr;
    return p_class_get_method_from_name(k, name, argc);
}

void* field(void* k, const char* name) {
    if (!k || !p_class_get_field_from_name) return nullptr;
    return p_class_get_field_from_name(k, name);
}

void* invoke(void* m, void* obj, void** params) {
    if (!m || !p_runtime_invoke) return nullptr;
    return p_runtime_invoke(m, obj, params, nullptr);
}

void* newObject(void* k) {
    if (!k || !p_object_new) return nullptr;
    return p_object_new(k);
}

void* readListItems(void* obj, uint32_t itemsOffset) {
    if (!obj) return nullptr;
    return *(void**)((uintptr_t)obj + itemsOffset);
}

int readListCount(void* obj, uint32_t countOffset) {
    if (!obj) return 0;
    return *(int*)((uintptr_t)obj + countOffset);
}

Matrix4x4 getViewProjection() {
    Matrix4x4 out = {0};
    void* camK = klass("", GameData::kCameraClass);
    if (!camK) return out;
    void* mainM = method(camK, GameData::kGetMainCamera, 0);
    if (!mainM) return out;
    void* cam = invoke(mainM, nullptr, nullptr);
    if (!cam) return out;

    Matrix4x4 proj = *(Matrix4x4*)((uintptr_t)cam + GameData::Off::ProjMatrix());
    Matrix4x4 view = *(Matrix4x4*)((uintptr_t)cam + GameData::Off::ViewMatrix());

    for (int r = 0; r < 4; r++) {
        for (int c = 0; c < 4; c++) {
            float s = 0;
            for (int k = 0; k < 4; k++)
                s += proj.m[r*4+k] * view.m[k*4+c];
            out.m[r*4+c] = s;
        }
    }
    return out;
}

}
""")

w("Src/ESP.h", r"""
#ifndef RAVEN_ESP_H
#define RAVEN_ESP_H
#import <UIKit/UIKit.h>
#import <QuartzCore/QuartzCore.h>
#include "Common.h"

@interface RavenESP : NSObject
@property (nonatomic, strong) UIWindow *window;
@property (nonatomic, strong) CAShapeLayer *boxes;
@property (nonatomic, strong) CAShapeLayer *lines;
@property (nonatomic, strong) CATextLayer  *labels;

+ (instancetype)shared;
- (void)attach;
- (void)attachToScene;
- (void)begin;
- (void)end;
- (void)render;

- (void)drawBox:(CGRect)r color:(UIColor*)c;
- (void)drawLine:(CGPoint)a to:(CGPoint)b color:(UIColor*)c;
@end
#endif
""")

w("Src/ESP.mm", r"""
#import "ESP.h"
#import "GameData.h"
#import "IL2CPP.h"
#import "Settings.h"

@implementation RavenESP

+ (instancetype)shared {
    static RavenESP *s; static dispatch_once_t once;
    dispatch_once(&once, ^{ s = [RavenESP new]; });
    return s;
}

- (void)attach {
    if (self.window) return;
    self.window = [[UIWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
    self.window.windowLevel = UIWindowLevelNormal + 0.5;
    self.window.backgroundColor = [UIColor clearColor];
    self.window.userInteractionEnabled = NO;
    self.window.rootViewController = [UIViewController new];
    self.window.rootViewController.view.backgroundColor = [UIColor clearColor];
    self.window.hidden = YES;

    self.boxes = [CAShapeLayer layer];
    self.boxes.frame = self.window.bounds;
    self.boxes.fillColor = [UIColor clearColor].CGColor;
    self.boxes.lineWidth = 1.5;
    self.boxes.strokeColor = RAVEN_RED.CGColor;

    self.lines = [CAShapeLayer layer];
    self.lines.frame = self.window.bounds;
    self.lines.fillColor = [UIColor clearColor].CGColor;
    self.lines.lineWidth = 1.0;
    self.lines.strokeColor = RAVEN_RED.CGColor;

    self.labels = [CATextLayer layer];
    self.labels.frame = self.window.bounds;
    self.labels.foregroundColor = RAVEN_SILVER.CGColor;
    self.labels.fontSize = 11;
    self.labels.contentsScale = [UIScreen mainScreen].scale;
    self.labels.alignmentMode = kCAAlignmentLeft;

    [self.window.layer addSublayer:self.boxes];
    [self.window.layer addSublayer:self.lines];
    [self.window.layer addSublayer:self.labels];
}

- (void)attachToScene {
    if (!self.window) return;
    for (UIScene *s in [UIApplication sharedApplication].connectedScenes) {
        if ([s isKindOfClass:[UIWindowScene class]]) {
            if (s.activationState == UISceneActivationStateForegroundActive ||
                s.activationState == UISceneActivationStateForegroundInactive) {
                self.window.windowScene = (UIWindowScene *)s;
                self.window.hidden = !RavenSettings::espEnabled;
                return;
            }
        }
    }
}

- (void)begin { self.boxes.path = NULL; self.lines.path = NULL; }
- (void)end {}

- (void)drawBox:(CGRect)r color:(UIColor*)c {
    UIBezierPath *p = [UIBezierPath bezierPathWithRect:r];
    CGMutablePathRef cur = CGPathCreateMutableCopy(self.boxes.path ?: CGPathCreateMutable());
    CGPathAddPath(cur, NULL, p.CGPath);
    self.boxes.path = cur;
    CGPathRelease(cur);
    self.boxes.strokeColor = c.CGColor;
}

- (void)drawLine:(CGPoint)a to:(CGPoint)b color:(UIColor*)c {
    CGMutablePathRef cur = CGPathCreateMutableCopy(self.lines.path ?: CGPathCreateMutable());
    CGPathMoveToPoint(cur, NULL, a.x, a.y);
    CGPathAddLineToPoint(cur, NULL, b.x, b.y);
    self.lines.path = cur;
    CGPathRelease(cur);
    self.lines.strokeColor = c.CGColor;
}

- (void)render {
    if (!RavenSettings::espEnabled) return;
}

@end
""")

w("Src/Aimbot.h", r"""
#ifndef RAVEN_AIMBOT_H
#define RAVEN_AIMBOT_H
#include "Common.h"

namespace RavenAimbot {
    void setEnabled(bool on);
    void tick();
}
#endif
""")

w("Src/Aimbot.mm", r"""
#import "Aimbot.h"
#import "GameData.h"
#import "IL2CPP.h"
#import "Settings.h"

namespace RavenAimbot {
void setEnabled(bool on) { RavenSettings::aimEnabled = on; }
void tick() { if (!RavenSettings::aimEnabled) return; }
}
""")

w("Src/Menu.h", r"""
#ifndef RAVEN_MENU_H
#define RAVEN_MENU_H
#import <UIKit/UIKit.h>
#import <QuartzCore/QuartzCore.h>

@interface RavenWindow : UIWindow
@end

@interface RavenMenu : NSObject
+ (instancetype)shared;
- (void)start;
- (void)setVisible:(BOOL)v;
- (BOOL)isPanelOpen;
@end

@interface RVToggle : UIView
@property (nonatomic, assign) BOOL on;
@property (nonatomic, copy) void (^onChange)(BOOL);
- (void)setOn:(BOOL)on animated:(BOOL)animated;
@end

@interface RVSlider : UIView
@property (nonatomic, assign) float value;
@property (nonatomic, assign) float minValue;
@property (nonatomic, assign) float maxValue;
@property (nonatomic, copy) void (^onChange)(float);
@end

#endif
""")

w("Src/Menu.mm", r"""
#import "Menu.h"
#import "Common.h"
#import "Logos.h"
#import "ESP.h"
#import "Aimbot.h"
#import "IL2CPP.h"
#import "Updater.h"
#import "Settings.h"
#import <objc/runtime.h>

#define C_WIN      [UIColor colorWithRed:0.043 green:0.043 blue:0.055 alpha:0.97]
#define C_HEAD     [UIColor colorWithRed:0.051 green:0.051 blue:0.063 alpha:1.0]
#define C_SIDE     [UIColor colorWithRed:0.055 green:0.055 blue:0.071 alpha:1.0]
#define C_CARD     [UIColor colorWithRed:0.078 green:0.078 blue:0.090 alpha:1.0]
#define C_CARD_HI  [UIColor colorWithRed:0.098 green:0.098 blue:0.112 alpha:1.0]
#define C_BORDER   [UIColor colorWithRed:0.157 green:0.157 blue:0.165 alpha:1.0]
#define C_RED      [UIColor colorWithRed:0.835 green:0.122 blue:0.157 alpha:1.0]
#define C_RED_DIM  [UIColor colorWithRed:0.520 green:0.075 blue:0.098 alpha:1.0]
#define C_CRIMSON  [UIColor colorWithRed:0.290 green:0.067 blue:0.086 alpha:1.0]
#define C_TEXT     [UIColor colorWithRed:0.949 green:0.949 blue:0.957 alpha:1.0]
#define C_SEC      [UIColor colorWithRed:0.573 green:0.573 blue:0.608 alpha:1.0]
#define C_MUTE     [UIColor colorWithRed:0.384 green:0.384 blue:0.420 alpha:1.0]

static const CGFloat kRefW       = 860;
static const CGFloat kRefH       = 500;
static const CGFloat kHeaderH    = 84;
static const CGFloat kFooterH    = 28;
static const CGFloat kSidebarW   = 168;
static const CGFloat kPad        = 18;
static const CGFloat kCardGap    = 12;
static const CGFloat kCardRad    = 8;
static const CGFloat kTabH       = 40;
static const CGFloat kRowH       = 28;
static const CGFloat kRowHBig    = 46;
static const CGFloat kScaleMax   = 1.00;
static const CGFloat kScaleFloor = 0.40;

static NSCache* g_imgCache = nil;
typedef void(^ImgBlock)(UIImage*);

static NSString* diskPathFor(NSString* key) {
    NSString* dir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) firstObject];
    NSString* hash = [NSString stringWithFormat:@"%lu", (unsigned long)key.hash];
    return [dir stringByAppendingPathComponent:[hash stringByAppendingString:@".img"]];
}

static UIImage* loadCachedImage(const char* url) {
    if (!url || !*url) return nil;
    if (!g_imgCache) g_imgCache = [[NSCache alloc] init];
    NSString* key = [NSString stringWithUTF8String:url];
    UIImage* c = [g_imgCache objectForKey:key];
    if (c) return c;
    NSData* d = [NSData dataWithContentsOfFile:diskPathFor(key)];
    if (!d) return nil;
    UIImage* img = [UIImage imageWithData:d];
    if (img) [g_imgCache setObject:img forKey:key];
    return img;
}

static void loadLogoURLAsync(const char* url, ImgBlock cb) {
    if (!url || !*url) { if (cb) cb(nil); return; }
    UIImage* cached = loadCachedImage(url);
    if (cached) { if (cb) cb(cached); return; }
    if (cb) cb(nil);

    NSString* key = [NSString stringWithUTF8String:url];
    NSURL* u = [NSURL URLWithString:key];
    if (!u) return;

    NSURLSessionDataTask* task =
        [[NSURLSession sharedSession] dataTaskWithURL:u
                                    completionHandler:^(NSData* data, NSURLResponse* resp, NSError* err) {
        if (!data) return;
        UIImage* img = [UIImage imageWithData:data];
        if (!img) return;
        if (!g_imgCache) g_imgCache = [[NSCache alloc] init];
        [g_imgCache setObject:img forKey:key];
        [data writeToFile:diskPathFor(key) atomically:YES];
        dispatch_async(dispatch_get_main_queue(), ^{
            if (cb) cb(img);
        });
    }];
    [task resume];
}

static UIImage* cropNormalized(UIImage* img, CGRect n) {
    if (!img || !img.CGImage) return img;
    size_t w = CGImageGetWidth(img.CGImage);
    size_t h = CGImageGetHeight(img.CGImage);
    CGRect px = CGRectMake(n.origin.x * w,
                           n.origin.y * h,
                           n.size.width * w,
                           n.size.height * h);
    px = CGRectIntersection(px, CGRectMake(0, 0, w, h));
    if (CGRectIsEmpty(px)) return img;
    CGImageRef cg = CGImageCreateWithImageInRect(img.CGImage, px);
    if (!cg) return img;
    UIImage* out = [UIImage imageWithCGImage:cg scale:img.scale orientation:img.imageOrientation];
    CGImageRelease(cg);
    return out;
}

static UILabel* lbl(NSString* t, CGFloat sz, UIColor* c, BOOL bold) {
    UILabel* l = [UILabel new];
    l.text = t;
    l.textColor = c;
    l.font = bold ? [UIFont systemFontOfSize:sz weight:UIFontWeightSemibold]
                  : [UIFont systemFontOfSize:sz weight:UIFontWeightRegular];
    l.numberOfLines = 1;
    l.backgroundColor = [UIColor clearColor];
    return l;
}

// ==================================================================
// Landscape-only enforcement
// ==================================================================
static NSUInteger raven_landscape_mask(id self, SEL _cmd) {
    return UIInterfaceOrientationMaskLandscape;
}

static void forceLandscape(void) {
    Method m = class_getInstanceMethod([UIViewController class],
                                       @selector(supportedInterfaceOrientations));
    if (m) {
        method_setImplementation(m, (IMP)raven_landscape_mask);
    }
}

// ==================================================================
// RavenWindow
// ==================================================================
@implementation RavenWindow
- (instancetype)initWithFrame:(CGRect)frame {
    if ((self = [super initWithFrame:frame])) {
        self.multipleTouchEnabled = YES;
        self.exclusiveTouch = NO;
        self.backgroundColor = [UIColor clearColor];
    }
    return self;
}
- (UIView*)hitTest:(CGPoint)point withEvent:(UIEvent*)event {
    RavenMenu* m = [RavenMenu shared];
    if (!m) return nil;
    UIView* panel = [m valueForKey:@"panel"];
    UIView* ball  = [m valueForKey:@"ball"];
    if (panel && !panel.hidden && panel.alpha > 0.01) {
        CGPoint p = [panel convertPoint:point fromView:self];
        if ([panel pointInside:p withEvent:event]) {
            return [panel hitTest:p withEvent:event];
        }
    }
    if (ball && !ball.hidden && ball.alpha > 0.01) {
        CGPoint p = [ball convertPoint:point fromView:self];
        if ([ball pointInside:p withEvent:event]) {
            UIView* hit = [ball hitTest:p withEvent:event];
            if (hit) return hit;
        }
    }
    return nil;
}
@end

// ==================================================================
// RVToggle
// ==================================================================
@implementation RVToggle { UIView* _track; UIView* _knob; }
- (instancetype)init {
    if ((self = [super initWithFrame:CGRectMake(0, 0, 38, 20)])) {
        self.userInteractionEnabled = YES;

        _track = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 38, 20)];
        _track.layer.cornerRadius = 10;
        _track.layer.borderWidth = 1;
        _track.layer.borderColor = [UIColor colorWithWhite:1 alpha:0.06].CGColor;
        _track.backgroundColor = [UIColor colorWithRed:0.18 green:0.18 blue:0.20 alpha:1.0];
        [self addSubview:_track];

        _knob = [[UIView alloc] initWithFrame:CGRectMake(2, 2, 16, 16)];
        _knob.layer.cornerRadius = 8;
        _knob.backgroundColor = [UIColor colorWithWhite:0.96 alpha:1.0];
        _knob.layer.shadowColor = [UIColor blackColor].CGColor;
        _knob.layer.shadowOpacity = 0.35;
        _knob.layer.shadowRadius = 2;
        _knob.layer.shadowOffset = CGSizeMake(0, 1);
        [self addSubview:_knob];

        UITapGestureRecognizer* t = [[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(toggle)];
        t.cancelsTouchesInView = YES;
        [self addGestureRecognizer:t];
    }
    return self;
}
- (void)toggle {
    self.on = !self.on;
    [self applyStateAnimated:YES];
    if (self.onChange) self.onChange(self.on);
}
- (void)setOn:(BOOL)on { [self setOn:on animated:NO]; }
- (void)setOn:(BOOL)on animated:(BOOL)animated { _on = on; [self applyStateAnimated:animated]; }
- (void)applyStateAnimated:(BOOL)animated {
    UIColor* track = _on ? C_RED : [UIColor colorWithRed:0.18 green:0.18 blue:0.20 alpha:1.0];
    CGRect knob = _on ? CGRectMake(38 - 18, 2, 16, 16) : CGRectMake(2, 2, 16, 16);
    void (^blk)(void) = ^{
        _track.backgroundColor = track;
        _knob.frame = knob;
    };
    if (animated) [UIView animateWithDuration:0.18 animations:blk];
    else blk();
}
@end

// ==================================================================
// RVSlider
// ==================================================================
@implementation RVSlider { UIView* _track; UIView* _fill; UIView* _thumb; float _t; }
- (instancetype)init {
    if ((self = [super initWithFrame:CGRectMake(0, 0, 200, 20)])) {
        self.userInteractionEnabled = YES;
        _minValue = 0; _maxValue = 100; _value = 0; _t = 0;

        _track = [UIView new];
        _track.backgroundColor = [UIColor colorWithRed:0.22 green:0.22 blue:0.25 alpha:1.0];
        _track.layer.cornerRadius = 1.5;
        [self addSubview:_track];

        _fill = [UIView new];
        _fill.backgroundColor = C_RED;
        _fill.layer.cornerRadius = 1.5;
        [self addSubview:_fill];

        _thumb = [UIView new];
        _thumb.backgroundColor = [UIColor colorWithWhite:0.98 alpha:1.0];
        _thumb.layer.cornerRadius = 6;
        _thumb.layer.shadowColor = [UIColor blackColor].CGColor;
        _thumb.layer.shadowOpacity = 0.35;
        _thumb.layer.shadowRadius = 2;
        _thumb.layer.shadowOffset = CGSizeMake(0, 1);
        [self addSubview:_thumb];

        UIPanGestureRecognizer* p = [[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(onDrag:)];
        p.cancelsTouchesInView = YES;
        [self addGestureRecognizer:p];
        UITapGestureRecognizer* t = [[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(onTap:)];
        t.cancelsTouchesInView = YES;
        [self addGestureRecognizer:t];
    }
    return self;
}
- (void)layoutSubviews {
    [super layoutSubviews];
    CGFloat w = self.bounds.size.width;
    CGFloat h = self.bounds.size.height;
    CGFloat th = 3.0;
    CGFloat ty = (h - th) / 2.0;
    CGFloat padL = 8.0;
    CGFloat padR = 8.0;
    CGFloat usable = w - padL - padR;

    _track.frame = CGRectMake(padL, ty, usable, th);
    _fill.frame  = CGRectMake(padL, ty, usable * _t, th);

    CGFloat thumbX = padL + usable * _t - 6.0;
    _thumb.frame = CGRectMake(thumbX, (h - 12.0) / 2.0, 12.0, 12.0);
}
- (void)setValue:(float)value {
    float v = MAX(_minValue, MIN(_maxValue, value));
    _value = v;
    _t = (_maxValue == _minValue) ? 0 : (v - _minValue) / (_maxValue - _minValue);
    [self setNeedsLayout];
}
- (void)onDrag:(UIPanGestureRecognizer*)g {
    CGPoint p = [g locationInView:self];
    CGFloat w = self.bounds.size.width;
    CGFloat padL = 8.0, padR = 8.0;
    CGFloat frac = MAX(0, MIN(1, (p.x - padL) / (w - padL - padR)));
    float v = _minValue + frac * (_maxValue - _minValue);
    self.value = v;
    if (self.onChange) self.onChange(v);
}
- (void)onTap:(UITapGestureRecognizer*)g {
    CGPoint p = [g locationInView:self];
    CGFloat w = self.bounds.size.width;
    CGFloat padL = 8.0, padR = 8.0;
    CGFloat frac = MAX(0, MIN(1, (p.x - padL) / (w - padL - padR)));
    float v = _minValue + frac * (_maxValue - _minValue);
    self.value = v;
    if (self.onChange) self.onChange(v);
}
@end

// ==================================================================
// RavenMenu
// ==================================================================
@interface RavenMenu ()
@property (nonatomic, strong) RavenWindow* window;
@property (nonatomic, strong, readwrite) UIView* panel;
@property (nonatomic, strong, readwrite) UIView* ball;
@property (nonatomic, strong) UIView*   panelInner;
@property (nonatomic, strong) UIView*   headerView;
@property (nonatomic, strong) UIView*   sidebarView;
@property (nonatomic, strong) UIView*   contentView;
@property (nonatomic, strong) UIView*   footerView;
@property (nonatomic, strong) NSMutableArray* tabButtons;
@property (nonatomic, strong) NSMutableDictionary* tabViews;
@property (nonatomic, assign) NSInteger activeTab;
@property (nonatomic, strong) NSTimer* tickTimer;
@property (nonatomic, assign) BOOL panelOpen;
@property (nonatomic, assign) BOOL runtimeActive;
@property (nonatomic, assign) CGFloat uiScale;
@property (nonatomic, assign) CGSize  lastBounds;
@property (nonatomic, assign) CGRect  dragStartFrame;
@end

@implementation RavenMenu

+ (instancetype)shared {
    static RavenMenu* s; static dispatch_once_t once;
    dispatch_once(&once, ^{ s = [RavenMenu new]; });
    return s;
}

- (BOOL)isPanelOpen { return self.panelOpen; }

- (void)start {
    if (self.window) return;
    [[RavenESP shared] attach];

    forceLandscape();

    self.tabButtons    = [NSMutableArray array];
    self.tabViews      = [NSMutableDictionary dictionary];
    self.activeTab     = 0;
    self.uiScale       = 1.0;
    self.lastBounds    = CGSizeZero;

    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        loadCachedImage(kWordmarkURL);
        loadCachedImage(kBallLogoURL);
        loadCachedImage(kEmblemURL);
        loadLogoURLAsync(kWordmarkURL, ^(UIImage* i){ (void)i; });
        loadLogoURLAsync(kBallLogoURL,   ^(UIImage* i){ (void)i; });
        loadLogoURLAsync(kEmblemURL,     ^(UIImage* i){ (void)i; });
    });

    self.window = [[RavenWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
    self.window.windowLevel = UIWindowLevelAlert + 100;
    self.window.backgroundColor = [UIColor clearColor];
    self.window.rootViewController = [UIViewController new];
    self.window.rootViewController.view.backgroundColor = [UIColor clearColor];
    self.window.rootViewController.view.userInteractionEnabled = NO;
    self.window.hidden = NO;
    [self attachToScene];

    if (@available(iOS 16.0, *)) {
        UIWindowScene* scene = self.window.windowScene;
        if (scene) {
            UIWindowSceneGeometryPreferencesIOS* prefs =
                [[UIWindowSceneGeometryPreferencesIOS alloc] initWithInterfaceOrientations:UIInterfaceOrientationMaskLandscape];
            [scene requestGeometryUpdateWithPreferences:prefs errorHandler:nil];
        }
    } else {
        [[UIDevice currentDevice] setValue:@(UIInterfaceOrientationLandscapeRight) forKey:@"orientation"];
    }

    [self buildPanel];
    [self buildBall];
    [self relayout];

    self.panel.hidden = YES;
    self.ball.hidden  = NO;
    self.runtimeActive = true;

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(onGeometryChanged)
                                                 name:UIDeviceOrientationDidChangeNotification
                                               object:nil];
    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(onGeometryChanged)
                                                 name:@"UIWindowSceneDidUpdateCoordinateSpaceNotification"
                                               object:nil];

    self.tickTimer = [NSTimer scheduledTimerWithTimeInterval:1.0/30.0
                                                      target:self
                                                    selector:@selector(onTick)
                                                    userInfo:nil
                                                     repeats:YES];
    RAVEN_LOG("menu started (landscape only)");
}

- (void)dealloc { [[NSNotificationCenter defaultCenter] removeObserver:self]; }

- (void)attachToScene {
    for (UIScene* s in [UIApplication sharedApplication].connectedScenes) {
        if ([s isKindOfClass:[UIWindowScene class]]) {
            if (s.activationState == UISceneActivationStateForegroundActive ||
                s.activationState == UISceneActivationStateForegroundInactive) {
                self.window.windowScene = (UIWindowScene*)s;
                return;
            }
        }
    }
}

- (void)setVisible:(BOOL)v { self.window.hidden = !v; }

- (void)onGeometryChanged {
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.08 * NSEC_PER_SEC)),
                   dispatch_get_main_queue(), ^{
        [self relayout];
        [self clampPanel];
    });
}

- (void)relayout {
    if (!self.window) return;
    CGRect screen = self.window.bounds;
    if (screen.size.width < 1 || screen.size.height < 1) return;

    UIEdgeInsets safe = self.window.safeAreaInsets;
    CGFloat usableW = screen.size.width - safe.left - safe.right;
    CGFloat usableH = screen.size.height - safe.top - safe.bottom;

    CGFloat fit = MIN(usableW / kRefW, usableH / kRefH);
    fit = MIN(fit, kScaleMax);
    fit = MAX(fit, kScaleFloor);
    self.uiScale = fit;

    CGFloat panelW = kRefW * fit;
    CGFloat panelH = kRefH * fit;
    if (panelW > usableW) panelW = usableW;
    if (panelH > usableH) panelH = usableH;

    CGFloat panelX = safe.left + (usableW - panelW) / 2;
    CGFloat panelY = safe.top  + (usableH - panelH) / 2;

    self.panel.transform = CGAffineTransformIdentity;
    self.panel.frame = CGRectMake(panelX, panelY, panelW, panelH);

    CGFloat sx = panelW / kRefW;
    CGFloat sy = panelH / kRefH;
    self.panelInner.bounds = CGRectMake(0, 0, kRefW, kRefH);
    self.panelInner.transform = CGAffineTransformIdentity;
    self.panelInner.transform = CGAffineTransformMakeScale(sx, sy);
    self.panelInner.center = CGPointMake(panelW / 2.0, panelH / 2.0);

    CGFloat bsize = 46;
    if (!self.ball.hidden) {
        CGFloat bx = screen.size.width - safe.right - bsize - 16;
        CGFloat by = safe.top + 24;
        bx = MAX(safe.left + 4, MIN(screen.size.width - safe.right - bsize - 4, bx));
        by = MAX(safe.top + 4,  MIN(screen.size.height - safe.bottom - bsize - 4, by));
        self.ball.frame = CGRectMake(bx, by, bsize, bsize);
    }
}

- (void)clampPanel {
    if (!self.window || self.panel.hidden) return;
    CGRect screen = self.window.bounds;
    UIEdgeInsets safe = self.window.safeAreaInsets;
    CGRect f = self.panel.frame;

    CGFloat maxW = screen.size.width - safe.left - safe.right;
    CGFloat maxH = screen.size.height - safe.top - safe.bottom;
    if (f.size.width  > maxW) f.size.width  = maxW;
    if (f.size.height > maxH) f.size.height = maxH;

    CGFloat minX = safe.left;
    CGFloat maxX = screen.size.width - safe.right - f.size.width;
    CGFloat minY = safe.top;
    CGFloat maxY = screen.size.height - safe.bottom - f.size.height;
    if (maxX < minX) maxX = minX;
    if (maxY < minY) maxY = minY;
    f.origin.x = MAX(minX, MIN(maxX, f.origin.x));
    f.origin.y = MAX(minY, MIN(maxY, f.origin.y));
    self.panel.frame = f;
}

- (void)centerPanel {
    if (!self.window) return;
    CGRect screen = self.window.bounds;
    UIEdgeInsets safe = self.window.safeAreaInsets;
    CGFloat usableW = screen.size.width - safe.left - safe.right;
    CGFloat usableH = screen.size.height - safe.top - safe.bottom;
    CGRect f = self.panel.frame;
    f.origin.x = safe.left + (usableW - f.size.width) / 2;
    f.origin.y = safe.top  + (usableH - f.size.height) / 2;
    self.panel.frame = f;
}

- (void)buildBall {
    CGFloat size = 46;
    self.ball = [[UIView alloc] initWithFrame:CGRectMake(0, 0, size, size)];
    self.ball.backgroundColor = C_WIN;
    self.ball.layer.cornerRadius = size / 2.0;
    self.ball.layer.borderWidth = 1.5;
    self.ball.layer.borderColor = C_RED.CGColor;
    self.ball.layer.shadowColor = C_RED.CGColor;
    self.ball.layer.shadowOpacity = 0.6;
    self.ball.layer.shadowRadius = 10;
    self.ball.layer.shadowOffset = CGSizeZero;
    self.ball.userInteractionEnabled = YES;
    self.ball.multipleTouchEnabled = NO;

    UILabel* placeholder = [[UILabel alloc] initWithFrame:self.ball.bounds];
    placeholder.text = @"R";
    placeholder.textAlignment = NSTextAlignmentCenter;
    placeholder.font = [UIFont systemFontOfSize:20 weight:UIFontWeightBold];
    placeholder.textColor = C_RED;
    placeholder.tag = 700;
    [self.ball addSubview:placeholder];

    UIImageView* iv = [[UIImageView alloc] initWithFrame:CGRectInset(self.ball.bounds, 3, 3)];
    iv.contentMode = UIViewContentModeScaleAspectFill;
    iv.layer.cornerRadius = (size - 6) / 2.0;
    iv.clipsToBounds = YES;
    iv.userInteractionEnabled = NO;
    iv.hidden = YES;
    iv.tag = 701;
    [self.ball addSubview:iv];

    __weak UIImageView* weakIV = iv;
    __weak UILabel* weakPH = placeholder;
    loadLogoURLAsync(kBallLogoURL, ^(UIImage* img) {
        if (!img) return;
        weakIV.image = img;
        weakIV.hidden = NO;
        weakPH.hidden = YES;
    });

    UITapGestureRecognizer* tap = [[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(togglePanel)];
    tap.cancelsTouchesInView = YES;
    [self.ball addGestureRecognizer:tap];

    UIPanGestureRecognizer* pan = [[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(dragBall:)];
    pan.cancelsTouchesInView = YES;
    pan.maximumNumberOfTouches = 1;
    [self.ball addGestureRecognizer:pan];

    [self.window addSubview:self.ball];
}

- (void)togglePanel {
    self.panelOpen = !self.panelOpen;
    if (self.panelOpen) {
        [self centerPanel];
        self.panel.hidden = NO;
        self.ball.hidden  = YES;
        [self.window bringSubviewToFront:self.panel];
    } else {
        self.panel.hidden = YES;
        self.ball.hidden  = NO;
        [self.window bringSubviewToFront:self.ball];
    }
}

- (void)dragBall:(UIPanGestureRecognizer*)g {
    if (!self.window) return;
    CGRect screen = self.window.bounds;
    UIEdgeInsets safe = self.window.safeAreaInsets;
    CGPoint t = [g translationInView:self.window];
    CGPoint c = self.ball.center;
    c.x += t.x; c.y += t.y;
    CGFloat hs = self.ball.bounds.size.width / 2.0;
    c.x = MAX(safe.left + hs, MIN(screen.size.width - safe.right - hs, c.x));
    c.y = MAX(safe.top + hs,  MIN(screen.size.height - safe.bottom - hs, c.y));
    self.ball.center = c;
    [g setTranslation:CGPointZero inView:self.window];
}

- (void)buildPanel {
    self.panel = [[UIView alloc] initWithFrame:CGRectMake(0, 0, kRefW, kRefH)];
    self.panel.backgroundColor = C_WIN;
    self.panel.layer.cornerRadius = 12;
    self.panel.layer.borderWidth = 1;
    self.panel.layer.borderColor = C_CRIMSON.CGColor;
    self.panel.layer.shadowColor = [UIColor blackColor].CGColor;
    self.panel.layer.shadowOpacity = 0.7;
    self.panel.layer.shadowRadius = 24;
    self.panel.layer.shadowOffset = CGSizeMake(0, 8);
    self.panel.clipsToBounds = YES;
    self.panel.userInteractionEnabled = YES;

    self.panelInner = [[UIView alloc] initWithFrame:CGRectMake(0, 0, kRefW, kRefH)];
    self.panelInner.backgroundColor = [UIColor clearColor];
    [self.panel addSubview:self.panelInner];

    [self buildHeader:CGRectMake(0, 0, kRefW, kHeaderH)];
    [self buildSidebar:CGRectMake(0, kHeaderH, kSidebarW, kRefH - kHeaderH - kFooterH)];
    [self buildContent:CGRectMake(kSidebarW, kHeaderH, kRefW - kSidebarW, kRefH - kHeaderH - kFooterH)];
    [self buildFooter:CGRectMake(0, kRefH - kFooterH, kRefW, kFooterH)];

    [self.window addSubview:self.panel];
    [self selectTab:0];
}

- (void)buildHeader:(CGRect)r {
    self.headerView = [[UIView alloc] initWithFrame:r];
    self.headerView.backgroundColor = C_HEAD;
    self.headerView.clipsToBounds = YES;
    self.headerView.userInteractionEnabled = YES;

    UIView* line = [[UIView alloc] initWithFrame:CGRectMake(0, r.size.height - 1, r.size.width, 1)];
    line.backgroundColor = [C_RED colorWithAlphaComponent:0.35];
    [self.headerView addSubview:line];

    CGFloat controlsW = 96;
    CGFloat bannerY = 6;
    CGFloat bannerH = r.size.height - 12;

    // The source header asset contains large black padding above/below the
    // actual banner. Size the visible banner by the cropped artwork ratio.
    CGFloat artAspect = 6.43;
    CGFloat maxBannerW = r.size.width - controlsW - 28;
    CGFloat bannerW = MIN(maxBannerW, bannerH * artAspect);
    CGFloat bannerX = MAX(14, (r.size.width - controlsW - bannerW) / 2.0);

    UIImageView* wm = [[UIImageView alloc] initWithFrame:CGRectMake(bannerX, bannerY, bannerW, bannerH)];
    wm.contentMode = UIViewContentModeScaleAspectFit;
    wm.clipsToBounds = YES;
    wm.userInteractionEnabled = NO;
    wm.hidden = YES;
    wm.tag = 801;
    [self.headerView addSubview:wm];

    UILabel* fallback = lbl(@"RAVEN", 26, C_TEXT, YES);
    fallback.frame = CGRectMake(bannerX, 0, bannerW, r.size.height);
    fallback.tag = 800;
    [self.headerView addSubview:fallback];

    __weak UIImageView* weakWM = wm;
    __weak UILabel* weakFB = fallback;
    loadLogoURLAsync(kWordmarkURL, ^(UIImage* img) {
        if (!img) return;
        // Crop away the black canvas from Cnzjdjh.png so the actual
        // RAVEN banner fills the header instead of appearing as a thumbnail.
        weakWM.image = cropNormalized(img, CGRectMake(0.0, 0.286, 1.0, 0.364));
        weakWM.hidden = NO;
        weakFB.hidden = YES;
    });

    UIButton* close = [UIButton buttonWithType:UIButtonTypeSystem];
    close.frame = CGRectMake(r.size.width - 44, (r.size.height - 30)/2, 30, 30);
    [close setTitle:@"X" forState:UIControlStateNormal];
    [close setTitleColor:C_RED forState:UIControlStateNormal];
    close.titleLabel.font = [UIFont systemFontOfSize:15 weight:UIFontWeightBold];
    [close addTarget:self action:@selector(togglePanel) forControlEvents:UIControlEventTouchUpInside];
    [self.headerView addSubview:close];

    UIButton* min = [UIButton buttonWithType:UIButtonTypeSystem];
    min.frame = CGRectMake(r.size.width - 82, (r.size.height - 30)/2, 30, 30);
    [min setTitle:@"—" forState:UIControlStateNormal];
    [min setTitleColor:C_SEC forState:UIControlStateNormal];
    min.titleLabel.font = [UIFont systemFontOfSize:18 weight:UIFontWeightSemibold];
    [min addTarget:self action:@selector(togglePanel) forControlEvents:UIControlEventTouchUpInside];
    [self.headerView addSubview:min];

    UIPanGestureRecognizer* pg = [[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(onHeaderDrag:)];
    pg.cancelsTouchesInView = NO;
    pg.maximumNumberOfTouches = 1;
    [self.headerView addGestureRecognizer:pg];

    [self.panelInner addSubview:self.headerView];
}

- (void)onHeaderDrag:(UIPanGestureRecognizer*)g {
    if (g.state == UIGestureRecognizerStateBegan) {
        self.dragStartFrame = self.panel.frame;
    } else if (g.state == UIGestureRecognizerStateChanged) {
        CGPoint t = [g translationInView:self.window];
        CGRect f = self.dragStartFrame;
        f.origin.x += t.x; f.origin.y += t.y;
        self.panel.frame = f;
        [self clampPanel];
    }
}

- (NSArray*)tabDefs {
    return @[
        @{@"title":@"AIMBOT",   @"key":@"aimbot"},
        @{@"title":@"ESP",      @"key":@"esp"},
        @{@"title":@"VISUALS",  @"key":@"visuals"},
        @{@"title":@"WEAPON",   @"key":@"weapon"},
        @{@"title":@"MISC",     @"key":@"misc"},
        @{@"title":@"PLAYERS",  @"key":@"players"},
        @{@"title":@"SETTINGS", @"key":@"settings"},
    ];
}

- (void)buildSidebar:(CGRect)r {
    self.sidebarView = [[UIView alloc] initWithFrame:r];
    self.sidebarView.backgroundColor = C_SIDE;
    self.sidebarView.clipsToBounds = YES;

    UIImageView* bg = [[UIImageView alloc] initWithFrame:self.sidebarView.bounds];
    bg.contentMode = UIViewContentModeScaleAspectFill;
    bg.clipsToBounds = YES;
    bg.userInteractionEnabled = NO;
    bg.tag = 900;
    [self.sidebarView addSubview:bg];

    __weak UIImageView* weakBG = bg;
    loadLogoURLAsync(kEmblemURL, ^(UIImage* img) {
        if (!img) return;
        // vLJmsVo.png has wide black margins around the real vertical art.
        // Crop to the bordered artwork before AspectFill so it fills the
        // entire sidebar instead of looking like a poster inside a black box.
        weakBG.image = cropNormalized(img, CGRectMake(0.267, 0.016, 0.465, 0.955));
    });

    // Keep only a light readability tint. The source artwork is already dark.
    UIView* tint = [[UIView alloc] initWithFrame:self.sidebarView.bounds];
    tint.backgroundColor = [UIColor colorWithRed:0.02 green:0.02 blue:0.04 alpha:0.14];
    tint.userInteractionEnabled = NO;
    [self.sidebarView addSubview:tint];

    UIView* sep = [[UIView alloc] initWithFrame:CGRectMake(r.size.width - 1, 0, 1, r.size.height)];
    sep.backgroundColor = C_BORDER;
    [self.sidebarView addSubview:sep];

    NSArray* defs = [self tabDefs];
    CGFloat y = 14;
    for (NSInteger i = 0; i < defs.count; i++) {
        NSDictionary* d = defs[i];
        std::string k = std::string([d[@"key"] UTF8String]);
        if (!Updater::feature(k, true)) continue;

        UIButton* btn = [UIButton buttonWithType:UIButtonTypeCustom];
        btn.frame = CGRectMake(0, y, r.size.width - 1, kTabH);
        btn.tag = i;
        btn.backgroundColor = [UIColor clearColor];
        [btn addTarget:self action:@selector(onTabTap:) forControlEvents:UIControlEventTouchUpInside];

        UIView* accent = [[UIView alloc] initWithFrame:CGRectMake(0, 8, 2, kTabH - 16)];
        accent.backgroundColor = [UIColor clearColor];
        accent.layer.cornerRadius = 1;
        accent.tag = 990;
        [btn addSubview:accent];

        UILabel* label = lbl(d[@"title"], 13, C_SEC, NO);
        label.frame = CGRectMake(20, 0, btn.frame.size.width - 28, kTabH);
        label.tag = 991;
        [btn addSubview:label];

        [self.sidebarView addSubview:btn];
        [self.tabButtons addObject:btn];
        y += kTabH + 4;
    }

    // The sidebar artwork already contains the SEE MORE. BE BETTER. motto.
    // Do not draw a duplicate text label over the asset.

    [self.panelInner addSubview:self.sidebarView];
}

- (void)onTabTap:(UIButton*)b { [self selectTab:b.tag]; }

- (void)selectTab:(NSInteger)idx {
    self.activeTab = idx;
    for (UIButton* b in self.tabButtons) {
        BOOL active = (b.tag == idx);
        UIView*  accent = [b viewWithTag:990];
        UILabel* label  = [b viewWithTag:991];
        accent.backgroundColor = active ? C_RED : [UIColor clearColor];
        label.textColor = active ? C_TEXT : C_SEC;
        label.font = active
            ? [UIFont systemFontOfSize:13 weight:UIFontWeightSemibold]
            : [UIFont systemFontOfSize:13 weight:UIFontWeightRegular];
        b.backgroundColor = active ? [C_CRIMSON colorWithAlphaComponent:0.55] : [UIColor clearColor];
    }
    for (UIView* v in self.contentView.subviews) [v removeFromSuperview];

    NSArray* defs = [self tabDefs];
    if (idx < 0 || idx >= (NSInteger)defs.count) return;
    NSString* key = defs[idx][@"title"];
    UIView* content = self.tabViews[key];
    if (!content) {
        content = [self buildTabContent:key];
        self.tabViews[key] = content;
    }
    content.frame = self.contentView.bounds;
    [self.contentView addSubview:content];
}

- (void)buildContent:(CGRect)r {
    self.contentView = [[UIView alloc] initWithFrame:r];
    self.contentView.backgroundColor = [UIColor clearColor];
    self.contentView.clipsToBounds = YES;
    [self.panelInner addSubview:self.contentView];
}

- (UIView*)buildTabContent:(NSString*)tab {
    UIScrollView* sv = [[UIScrollView alloc] initWithFrame:self.contentView.bounds];
    sv.backgroundColor = [UIColor clearColor];
    sv.showsVerticalScrollIndicator = NO;
    sv.contentInsetAdjustmentBehavior = UIScrollViewContentInsetAdjustmentNever;

    CGFloat W = sv.bounds.size.width;

    UILabel* title = lbl(tab, 18, C_TEXT, YES);
    title.frame = CGRectMake(kPad, 14, W - kPad*2, 22);
    [sv addSubview:title];

    UILabel* sub = lbl([self subtitleForTab:tab], 11, C_SEC, NO);
    sub.frame = CGRectMake(kPad, 38, W - kPad*2, 15);
    [sv addSubview:sub];

    CGFloat startY = 68;
    CGFloat availW = W - kPad*2;
    BOOL twoCols = (availW >= 500);
    CGFloat colW = twoCols ? (availW - kCardGap) / 2.0 : availW;

    NSArray* cards = [self cardsForTab:tab width:colW];
    CGFloat leftY = startY;
    CGFloat rightY = startY;

    for (NSInteger i = 0; i < (NSInteger)cards.count; i++) {
        UIView* c = cards[i];
        CGFloat h = c.frame.size.height;
        if (twoCols && (i % 2) == 0) {
            c.frame = CGRectMake(kPad, leftY, colW, h);
            leftY += h + kCardGap;
        } else if (twoCols) {
            c.frame = CGRectMake(kPad + colW + kCardGap, rightY, colW, h);
            rightY += h + kCardGap;
        } else {
            c.frame = CGRectMake(kPad, leftY, colW, h);
            leftY += h + kCardGap;
        }
        [sv addSubview:c];
    }
    CGFloat contentH = MAX(leftY, rightY) + kPad;
    sv.contentSize = CGSizeMake(W, contentH);
    return sv;
}

- (NSString*)subtitleForTab:(NSString*)tab {
    if ([tab isEqualToString:@"AIMBOT"])   return @"Configure targeting and aim behavior";
    if ([tab isEqualToString:@"ESP"])      return @"Player visibility and overlay options";
    if ([tab isEqualToString:@"VISUALS"])  return @"Screen and rendering adjustments";
    if ([tab isEqualToString:@"WEAPON"])   return @"Weapon behavior modifications";
    if ([tab isEqualToString:@"MISC"])     return @"Movement, utility and interface tweaks";
    if ([tab isEqualToString:@"PLAYERS"])  return @"Nearby player list";
    if ([tab isEqualToString:@"SETTINGS"]) return @"Menu configuration and about";
    return @"";
}

- (UIView*)card:(NSString*)title width:(CGFloat)w rows:(NSArray*)rows {
    UIView* card = [UIView new];
    card.backgroundColor = C_CARD;
    card.layer.cornerRadius = kCardRad;
    card.layer.borderWidth = 1;
    card.layer.borderColor = C_BORDER.CGColor;

    UILabel* t = lbl(title, 11, C_RED, YES);
    t.frame = CGRectMake(14, 11, w - 28, 14);
    [card addSubview:t];

    UIView* line = [[UIView alloc] initWithFrame:CGRectMake(14, 28, w - 28, 1)];
    line.backgroundColor = [C_RED colorWithAlphaComponent:0.12];
    [card addSubview:line];

    CGFloat y = 36;
    for (UIView* r in rows) {
        CGFloat rh = r.frame.size.height;
        r.frame = CGRectMake(0, y, w, rh);
        [card addSubview:r];
        y += rh;
    }
    y += 8;
    card.frame = CGRectMake(0, 0, w, y);
    return card;
}

- (UIView*)rowToggle:(NSString*)title on:(BOOL)on cb:(void(^)(BOOL))cb {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, kRowH)];
    UILabel* l = lbl(title, 13, C_TEXT, NO);
    l.frame = CGRectMake(14, 0, 160, kRowH);
    [row addSubview:l];
    RVToggle* t = [[RVToggle alloc] init];
    t.on = on;
    t.onChange = cb;
    t.frame = CGRectMake(row.frame.size.width - 52, (kRowH - 20) / 2.0, 38, 20);
    t.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    [row addSubview:t];
    return row;
}

- (UIView*)rowSlider:(NSString*)title min:(float)mn max:(float)mx val:(float)v cb:(void(^)(float))cb {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, kRowHBig)];
    UILabel* l = lbl(title, 13, C_TEXT, NO);
    l.frame = CGRectMake(14, 4, 170, 18);
    [row addSubview:l];

    UILabel* val = lbl([NSString stringWithFormat:@"%.0f", v], 12, C_RED, YES);
    val.textAlignment = NSTextAlignmentRight;
    val.frame = CGRectMake(row.frame.size.width - 68, 4, 54, 18);
    val.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    [row addSubview:val];

    RVSlider* s = [[RVSlider alloc] init];
    s.minValue = mn; s.maxValue = mx; s.value = v;
    s.frame = CGRectMake(14, 26, row.frame.size.width - 28, 18);
    s.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    s.onChange = ^(float nv) {
        val.text = [NSString stringWithFormat:@"%.0f", nv];
        if (cb) cb(nv);
    };
    [row addSubview:s];
    return row;
}

- (UIView*)rowDropdown:(NSString*)title value:(NSString*)val {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, kRowH)];
    UILabel* l = lbl(title, 13, C_TEXT, NO);
    l.frame = CGRectMake(14, 0, 140, kRowH);
    [row addSubview:l];

    UIView* pill = [[UIView alloc] initWithFrame:CGRectMake(row.frame.size.width - 100, 4, 86, 20)];
    pill.backgroundColor = [UIColor colorWithRed:0.10 green:0.10 blue:0.11 alpha:1.0];
    pill.layer.cornerRadius = 4;
    pill.layer.borderWidth = 1;
    pill.layer.borderColor = C_BORDER.CGColor;
    pill.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    [row addSubview:pill];

    UILabel* v = lbl(val, 11, C_TEXT, NO);
    v.textAlignment = NSTextAlignmentCenter;
    v.frame = pill.bounds;
    [pill addSubview:v];
    return row;
}

- (UIView*)rowInfo:(NSString*)title value:(NSString*)val {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, kRowH)];
    UILabel* l = lbl(title, 13, C_TEXT, NO);
    l.frame = CGRectMake(14, 0, 140, kRowH);
    [row addSubview:l];
    UILabel* v = lbl(val, 12, C_RED, YES);
    v.textAlignment = NSTextAlignmentRight;
    v.frame = CGRectMake(row.frame.size.width - 160, 0, 146, kRowH);
    v.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    [row addSubview:v];
    return row;
}

- (UIView*)rowButton:(NSString*)title tap:(void(^)(void))cb {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, 36)];
    UIButton* b = [UIButton buttonWithType:UIButtonTypeCustom];
    b.frame = CGRectMake(12, 2, row.frame.size.width - 24, 32);
    b.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    [b setTitle:title forState:UIControlStateNormal];
    [b setTitleColor:C_TEXT forState:UIControlStateNormal];
    b.titleLabel.font = [UIFont systemFontOfSize:12 weight:UIFontWeightMedium];
    b.backgroundColor = [UIColor colorWithWhite:0.11 alpha:1.0];
    b.layer.cornerRadius = 6;
    b.layer.borderWidth = 1;
    b.layer.borderColor = C_BORDER.CGColor;
    b.tag = (NSInteger)CFBridgingRetain([cb copy]);
    [b addTarget:self action:@selector(onGenericButton:) forControlEvents:UIControlEventTouchUpInside];
    [row addSubview:b];
    return row;
}

- (void)onGenericButton:(UIButton*)b {
    void (^cb)(void) = (__bridge void (^)(void))(void*)b.tag;
    if (cb) cb();
}

- (NSArray*)cardsForTab:(NSString*)tab width:(CGFloat)w {
    if ([tab isEqualToString:@"AIMBOT"]) {
        UIView* general = [self card:@"GENERAL" width:w rows:@[
            [self rowToggle:@"Enable Aimbot" on:RavenSettings::aimEnabled cb:^(BOOL v){ RavenSettings::aimEnabled = v; RavenSettings::save(); }],
            [self rowDropdown:@"Aim Activation" value:@"Hold"],
            [self rowSlider:@"Aim FOV" min:0 max:360 val:RavenSettings::aimFov cb:^(float v){ RavenSettings::aimFov = v; }],
            [self rowSlider:@"Smoothness" min:1 max:30 val:RavenSettings::aimSmooth cb:^(float v){ RavenSettings::aimSmooth = v; }],
        ]];
        UIView* advanced = [self card:@"ADVANCED" width:w rows:@[
            [self rowToggle:@"Prediction" on:RavenSettings::aimPrediction cb:^(BOOL v){ RavenSettings::aimPrediction = v; }],
            [self rowSlider:@"Aim Delay" min:0 max:300 val:RavenSettings::aimDelay cb:^(float v){ RavenSettings::aimDelay = v; }],
            [self rowSlider:@"Target Switch Delay" min:0 max:500 val:RavenSettings::aimSwitchDelay cb:^(float v){ RavenSettings::aimSwitchDelay = v; }],
        ]];
        UIView* targeting = [self card:@"TARGETING" width:w rows:@[
            [self rowDropdown:@"Target Bone" value:@"Head"],
            [self rowDropdown:@"Target Priority" value:@"Distance"],
            [self rowToggle:@"Visible Check" on:RavenSettings::aimVisCheck cb:^(BOOL v){ RavenSettings::aimVisCheck = v; }],
            [self rowSlider:@"Max Distance" min:50 max:500 val:RavenSettings::aimMaxDist cb:^(float v){ RavenSettings::aimMaxDist = v; }],
        ]];
        UIView* fovCard = [self card:@"FOV" width:w rows:@[
            [self rowToggle:@"Show FOV Circle" on:RavenSettings::aimShowCircle cb:^(BOOL v){ RavenSettings::aimShowCircle = v; }],
            [self rowSlider:@"FOV Radius" min:20 max:400 val:RavenSettings::aimCircleRadius cb:^(float v){ RavenSettings::aimCircleRadius = v; }],
            [self rowSlider:@"Circle Thickness" min:1 max:6 val:RavenSettings::aimCircleThickness cb:^(float v){ RavenSettings::aimCircleThickness = v; }],
        ]];
        return @[general, targeting, advanced, fovCard];
    }

    if ([tab isEqualToString:@"ESP"]) {
        UIView* player = [self card:@"PLAYER ESP" width:w rows:@[
            [self rowToggle:@"Enable ESP" on:RavenSettings::espEnabled cb:^(BOOL v){ RavenSettings::espEnabled = v; RavenSettings::save(); }],
            [self rowToggle:@"Box" on:RavenSettings::espBox cb:^(BOOL v){ RavenSettings::espBox = v; }],
            [self rowToggle:@"Corner Box" on:RavenSettings::espCorner cb:^(BOOL v){ RavenSettings::espCorner = v; }],
            [self rowToggle:@"Skeleton" on:RavenSettings::espSkeleton cb:^(BOOL v){ RavenSettings::espSkeleton = v; }],
            [self rowToggle:@"Snaplines" on:RavenSettings::espSnaplines cb:^(BOOL v){ RavenSettings::espSnaplines = v; }],
        ]];
        UIView* info = [self card:@"INFORMATION" width:w rows:@[
            [self rowToggle:@"Name" on:RavenSettings::espName cb:^(BOOL v){ RavenSettings::espName = v; }],
            [self rowToggle:@"Distance" on:RavenSettings::espDistance cb:^(BOOL v){ RavenSettings::espDistance = v; }],
            [self rowToggle:@"Health" on:RavenSettings::espHealth cb:^(BOOL v){ RavenSettings::espHealth = v; }],
            [self rowToggle:@"Weapon" on:RavenSettings::espWeapon cb:^(BOOL v){ RavenSettings::espWeapon = v; }],
        ]];
        UIView* colors = [self card:@"COLORS" width:w rows:@[
            [self rowDropdown:@"Enemy Color" value:@"Red"],
            [self rowDropdown:@"Visible Color" value:@"Green"],
            [self rowDropdown:@"Skeleton Color" value:@"White"],
            [self rowDropdown:@"Box Color" value:@"Red"],
        ]];
        return @[player, info, colors];
    }

    if ([tab isEqualToString:@"VISUALS"]) {
        UIView* cross = [self card:@"CROSSHAIR" width:w rows:@[
            [self rowToggle:@"Enable Crosshair" on:RavenSettings::visCrosshair cb:^(BOOL v){ RavenSettings::visCrosshair = v; }],
            [self rowDropdown:@"Style" value:@"Dot"],
            [self rowSlider:@"Size" min:1 max:30 val:RavenSettings::visCrosshairSize cb:^(float v){ RavenSettings::visCrosshairSize = v; }],
            [self rowSlider:@"Thickness" min:1 max:6 val:RavenSettings::visCrosshairThickness cb:^(float v){ RavenSettings::visCrosshairThickness = v; }],
        ]];
        UIView* fov = [self card:@"FOV CIRCLE" width:w rows:@[
            [self rowToggle:@"Enable" on:RavenSettings::visFovCircle cb:^(BOOL v){ RavenSettings::visFovCircle = v; }],
            [self rowSlider:@"Radius" min:20 max:400 val:RavenSettings::visFovRadius cb:^(float v){ RavenSettings::visFovRadius = v; }],
            [self rowSlider:@"Thickness" min:1 max:6 val:RavenSettings::visFovThickness cb:^(float v){ RavenSettings::visFovThickness = v; }],
        ]];
        UIView* world = [self card:@"WORLD VISUALS" width:w rows:@[
            [self rowToggle:@"Remove Fog" on:RavenSettings::visRemoveFog cb:^(BOOL v){ RavenSettings::visRemoveFog = v; }],
            [self rowToggle:@"Night Mode" on:RavenSettings::visNightMode cb:^(BOOL v){ RavenSettings::visNightMode = v; }],
            [self rowToggle:@"Brightness Boost" on:RavenSettings::visBrightnessBoost cb:^(BOOL v){ RavenSettings::visBrightnessBoost = v; }],
            [self rowSlider:@"Brightness" min:0 max:200 val:RavenSettings::visBrightness cb:^(float v){ RavenSettings::visBrightness = v; }],
        ]];
        UIView* display = [self card:@"DISPLAY" width:w rows:@[
            [self rowToggle:@"No Flash" on:RavenSettings::visNoFlash cb:^(BOOL v){ RavenSettings::visNoFlash = v; }],
            [self rowToggle:@"No Smoke" on:RavenSettings::visNoSmoke cb:^(BOOL v){ RavenSettings::visNoSmoke = v; }],
            [self rowToggle:@"Better Textures" on:RavenSettings::visBetterTextures cb:^(BOOL v){ RavenSettings::visBetterTextures = v; }],
        ]];
        return @[cross, fov, world, display];
    }

    if ([tab isEqualToString:@"WEAPON"]) {
        UIView* recoil = [self card:@"RECOIL" width:w rows:@[
            [self rowToggle:@"No Recoil" on:RavenSettings::wpnNoRecoil cb:^(BOOL v){ RavenSettings::wpnNoRecoil = v; }],
            [self rowToggle:@"No Spread" on:RavenSettings::wpnNoSpread cb:^(BOOL v){ RavenSettings::wpnNoSpread = v; }],
            [self rowSlider:@"Recoil Strength" min:0 max:100 val:RavenSettings::wpnRecoilStrength cb:^(float v){ RavenSettings::wpnRecoilStrength = v; }],
        ]];
        UIView* handling = [self card:@"HANDLING" width:w rows:@[
            [self rowToggle:@"Fast Reload" on:RavenSettings::wpnFastReload cb:^(BOOL v){ RavenSettings::wpnFastReload = v; }],
            [self rowToggle:@"Rapid Fire" on:RavenSettings::wpnRapidFire cb:^(BOOL v){ RavenSettings::wpnRapidFire = v; }],
            [self rowSlider:@"Fire Rate Multiplier" min:1 max:10 val:RavenSettings::wpnFireRate cb:^(float v){ RavenSettings::wpnFireRate = v; }],
        ]];
        UIView* effects = [self card:@"EFFECTS" width:w rows:@[
            [self rowToggle:@"No Flash" on:RavenSettings::wpnNoFlash cb:^(BOOL v){ RavenSettings::wpnNoFlash = v; }],
            [self rowToggle:@"No Smoke" on:RavenSettings::wpnNoSmoke cb:^(BOOL v){ RavenSettings::wpnNoSmoke = v; }],
            [self rowToggle:@"No Shell Casings" on:RavenSettings::wpnNoShells cb:^(BOOL v){ RavenSettings::wpnNoShells = v; }],
        ]];
        return @[recoil, handling, effects];
    }

    if ([tab isEqualToString:@"MISC"]) {
        UIView* movement = [self card:@"MOVEMENT" width:w rows:@[
            [self rowToggle:@"Bunny Hop" on:RavenSettings::miscBunnyHop cb:^(BOOL v){ RavenSettings::miscBunnyHop = v; }],
            [self rowToggle:@"Auto Strafe" on:RavenSettings::miscAutoStrafe cb:^(BOOL v){ RavenSettings::miscAutoStrafe = v; }],
            [self rowToggle:@"No Fall Damage" on:RavenSettings::miscNoFallDamage cb:^(BOOL v){ RavenSettings::miscNoFallDamage = v; }],
        ]];
        UIView* utility = [self card:@"UTILITY" width:w rows:@[
            [self rowToggle:@"Unlock All" on:RavenSettings::miscUnlockAll cb:^(BOOL v){ RavenSettings::miscUnlockAll = v; }],
            [self rowToggle:@"No Ads" on:RavenSettings::miscNoAds cb:^(BOOL v){ RavenSettings::miscNoAds = v; }],
            [self rowToggle:@"Panic Key" on:RavenSettings::miscPanicKey cb:^(BOOL v){ RavenSettings::miscPanicKey = v; }],
        ]];
        UIView* iface = [self card:@"INTERFACE" width:w rows:@[
            [self rowToggle:@"Hide Menu When Closed" on:RavenSettings::miscHideWhenClosed cb:^(BOOL v){ RavenSettings::miscHideWhenClosed = v; }],
            [self rowSlider:@"Menu Opacity" min:20 max:100 val:RavenSettings::miscMenuOpacity cb:^(float v){ RavenSettings::miscMenuOpacity = v; }],
        ]];
        return @[movement, utility, iface];
    }

    if ([tab isEqualToString:@"PLAYERS"]) {
        UILabel* empty = lbl(@"No player data available", 12, C_SEC, NO);
        empty.textAlignment = NSTextAlignmentCenter;
        empty.frame = CGRectMake(0, 0, w - 28, 60);
        UIView* emptyRow = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, 60)];
        [emptyRow addSubview:empty];
        UIView* list = [self card:@"PLAYER LIST" width:w rows:@[emptyRow]];
        return @[list];
    }

    if ([tab isEqualToString:@"SETTINGS"]) {
        std::string rv = Updater::remoteVersion();
        NSString* rvStr = [NSString stringWithUTF8String:rv.c_str()];

        UIView* iface = [self card:@"INTERFACE" width:w rows:@[
            [self rowSlider:@"Menu Scale" min:50 max:150 val:RavenSettings::menuScale cb:^(float v){ RavenSettings::menuScale = v; }],
            [self rowDropdown:@"Accent Color" value:@"Crimson"],
            [self rowToggle:@"Animations" on:RavenSettings::animations cb:^(BOOL v){ RavenSettings::animations = v; }],
        ]];
        UIView* config = [self card:@"CONFIG" width:w rows:@[
            [self rowButton:@"Save Config" tap:^{ RavenSettings::save(); }],
            [self rowButton:@"Load Config" tap:^{ RavenSettings::load(); }],
            [self rowButton:@"Reset to Defaults" tap:^{ RavenSettings::save(); }],
        ]];
        UIView* menu = [self card:@"MENU" width:w rows:@[
            [self rowDropdown:@"Open/Close Button" value:@"Floating"],
            [self rowDropdown:@"Position" value:@"Right"],
            [self rowSlider:@"Opacity" min:20 max:100 val:RavenSettings::miscMenuOpacity cb:^(float v){ RavenSettings::miscMenuOpacity = v; }],
        ]];
        UIView* about = [self card:@"ABOUT" width:w rows:@[
            [self rowInfo:@"Version" value:rvStr],
            [self rowInfo:@"Brand" value:@"@KremCheats"],
            [self rowInfo:@"Developer" value:@"@Kremityss"],
            [self rowInfo:@"Status" value:[NSString stringWithUTF8String:Updater::status()]],
        ]];
        return @[iface, config, menu, about];
    }

    return @[];
}

- (void)buildFooter:(CGRect)r {
    self.footerView = [[UIView alloc] initWithFrame:r];
    self.footerView.backgroundColor = C_HEAD;

    UIView* top = [[UIView alloc] initWithFrame:CGRectMake(0, 0, r.size.width, 1)];
    top.backgroundColor = C_BORDER;
    [self.footerView addSubview:top];

    UIView* dot = [[UIView alloc] initWithFrame:CGRectMake(14, (r.size.height - 7)/2, 7, 7)];
    dot.backgroundColor = [UIColor colorWithRed:0.2 green:0.9 blue:0.3 alpha:1.0];
    dot.layer.cornerRadius = 3.5;
    [self.footerView addSubview:dot];

    UILabel* l = lbl(@"Connected", 10, C_SEC, NO);
    l.frame = CGRectMake(26, 0, 140, r.size.height);
    [self.footerView addSubview:l];

    UILabel* r2 = lbl(@"RAVEN  •  KREMCHEATS  •  v1.0", 10, C_RED, YES);
    r2.textAlignment = NSTextAlignmentRight;
    r2.frame = CGRectMake(r.size.width - 230, 0, 216, r.size.height);
    [self.footerView addSubview:r2];

    [self.panelInner addSubview:self.footerView];
}

- (void)onTick {
    if (!self.window) return;
    CGSize b = self.window.bounds.size;
    if (!CGSizeEqualToSize(b, self.lastBounds)) {
        self.lastBounds = b;
        [self relayout];
        [self clampPanel];
    }
    if (!self.runtimeActive) return;
    if (RavenSettings::espEnabled) [[RavenESP shared] render];
    if (RavenSettings::aimEnabled) RavenAimbot::tick();
}

@end
""")

print("done - Raven correction pass")
