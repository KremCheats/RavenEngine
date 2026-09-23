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
Raven_FILES = Raven.mm Src/IL2CPP.mm Src/ESP.mm Src/Aimbot.mm Src/Menu.mm
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

__attribute__((constructor))
static void raven_entry(void) {
    @autoreleasepool {
        RAVEN_LOG("entry");
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
#import <Foundation/Foundation.h>
#import <os/log.h>

#define RAVEN_LOG(fmt, ...) os_log(OS_LOG_DEFAULT, "[raven] " fmt, ##__VA_ARGS__)

struct Vec3 { float x, y, z; };
struct Matrix4x4 { float m[16]; };

// ---- Raven brand ----
#define RAVEN_RED    [UIColor colorWithRed:0.769 green:0.118 blue:0.118 alpha:1.0]  // #C41E1E
#define RAVEN_SILVER [UIColor colorWithRed:0.910 green:0.910 blue:0.910 alpha:1.0]  // #E8E8E8
#define RAVEN_BG     [UIColor colorWithRed:0.039 green:0.039 blue:0.039 alpha:0.95] // #0A0A0A
#define RAVEN_DARK   [UIColor colorWithRed:0.102 green:0.102 blue:0.102 alpha:1.0]  // #1A1A1A

#endif
""")

w("Src/GameData.h", r"""
#ifndef RAVEN_GAMEDATA_H
#define RAVEN_GAMEDATA_H

// ==================================================================
// FILL THESE IN FROM: https://github.com/AnzeLaCM/CombatMaster-Full-Offsets
// The names below are educated guesses. Run a dumper or read the
// offsets repo README to confirm each one for the current build.
// ==================================================================

namespace GameData {

    // ---- Class names ----
    static const char* kLocalPlayerClass = "PlayerRoot";     // TODO confirm
    static const char* kPlayerListClass  = "PlayerManager";  // TODO confirm
    static const char* kCameraClass      = "Camera";         // usually "Camera"
    static const char* kGameClass        = "GameManager";    // TODO confirm

    // ---- Method names ----
    static const char* kGetInstance     = "get_Instance";
    static const char* kGetLocalPlayer  = "get_LocalPlayer"; // TODO confirm
    static const char* kGetAllPlayers   = "get_AllPlayers";  // TODO confirm
    static const char* kGetMainCamera   = "get_main";

    // ---- Field names (used with IL2CPP::field) ----
    static const char* kFldHealth       = "Health";
    static const char* kFldArmor        = "Armor";
    static const char* kFldPosition     = "Position";
    static const char* kFldTeamId       = "TeamId";
    static const char* kFldIsVisible    = "IsVisible";
    static const char* kFldIsLocal      = "IsLocalPlayer";
    static const char* kFldName         = "PlayerName";

    // ---- List field (on kPlayerListClass) ----
    static const char* kFldPlayerList   = "AllPlayers";      // TODO confirm

    // ---- Field offsets — FILL FROM THE OFFSETS REPO ----
    // All values below are placeholders. Replace with actual hex.
    namespace Off {
        constexpr uint32_t Health      = 0x0;
        constexpr uint32_t Armor       = 0x0;
        constexpr uint32_t Position    = 0x0;
        constexpr uint32_t TeamId      = 0x0;
        constexpr uint32_t IsVisible   = 0x0;
        constexpr uint32_t IsLocal     = 0x0;

        constexpr uint32_t ListCount   = 0x18;  // List<T> size field, usually 0x18
        constexpr uint32_t ListItems   = 0x10;  // List<T> items pointer, usually 0x10
        constexpr uint32_t ArrayData   = 0x20;  // first element of object[]

        constexpr uint32_t ViewMatrix  = 0x0;
        constexpr uint32_t ProjMatrix  = 0x0;
    }

    // ---- Bone indices (HumanBodyBones) ----
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

// ==================================================================
// Paste base64 of your two logos between the quotes below.
// If left empty, the UI falls back to a drawn ball and text header.
//
// How to generate base64 on iPhone:
//   1. Open Shortcuts app
//   2. New shortcut: "Encode Image"
//   3. Actions: Get File → Base64 Encode (Line Breaks: None) → Copy to Clipboard
//   4. Run it, pick your logo file, paste here.
//
// Ball logo   = the round KREM target/crest image
// Header logo = the horizontal KREM CHEATS banner
// ==================================================================

static const char* kBallLogoB64   = "";
static const char* kHeaderLogoB64 = "";

#endif
""")

w("Src/IL2CPP.h", r"""
#ifndef RAVEN_IL2CPP_H
#define RAVEN_IL2CPP_H
#include <cstdint>
#include <string>
#include <vector>

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

    // Raw pointer read/write by offset
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

    // Read a Unity List<T> at a given field on the object
    void* readListItems(void* obj, uint32_t itemsOffset);
    int   readListCount(void* obj, uint32_t countOffset);

    // Camera
    Matrix4x4 getViewProjection();
}
#endif
""")

w("Src/IL2CPP.mm", r"""
#import "IL2CPP.h"
#import "Common.h"
#import "GameData.h"
#import <dlfcn.h>
#import <string.h>
#import <mach-o/dyld.h>
#import <mach-o/loader.h>

namespace IL2CPP {

// ---------- API typedefs ----------
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
    // Locate the Unity image
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
    if (!g_domain) {
        snprintf(g_status, sizeof(g_status), "null domain");
        return false;
    }
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

// Unity camera matrix read — Camera.main.projectionMatrix * Camera.main.worldToCameraMatrix
Matrix4x4 getViewProjection() {
    Matrix4x4 out = {0};
    void* camK = klass("", GameData::kCameraClass);
    if (!camK) return out;
    void* mainM = method(camK, GameData::kGetMainCamera, 0);
    if (!mainM) return out;
    void* cam = invoke(mainM, nullptr, nullptr);
    if (!cam) return out;

    Matrix4x4 proj = *(Matrix4x4*)((uintptr_t)cam + GameData::Off::ProjMatrix);
    Matrix4x4 view = *(Matrix4x4*)((uintptr_t)cam + GameData::Off::ViewMatrix);

    // out = proj * view
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
- (void)begin;
- (void)end;
- (void)render;

- (void)drawBox:(CGRect)r color:(UIColor*)c;
- (void)drawLine:(CGPoint)a to:(CGPoint)b color:(UIColor*)c;
- (void)drawText:(NSString*)s at:(CGPoint)p color:(UIColor*)c;

@end
#endif
""")

w("Src/ESP.mm", r"""
#import "ESP.h"
#import "GameData.h"
#import "IL2CPP.h"

@implementation RavenESP

+ (instancetype)shared {
    static RavenESP *s; static dispatch_once_t once;
    dispatch_once(&once, ^{ s = [RavenESP new]; });
    return s;
}

- (void)attach {
    if (self.window) return;
    self.window = [[UIWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
    self.window.windowLevel = UIWindowLevelNormal + 1;
    self.window.backgroundColor = [UIColor clearColor];
    self.window.userInteractionEnabled = NO;
    self.window.rootViewController = [UIViewController new];
    self.window.rootViewController.view.backgroundColor = [UIColor clearColor];
    self.window.hidden = YES;

    self.boxes  = [CAShapeLayer layer];
    self.boxes.frame = self.window.bounds;
    self.boxes.fillColor = [UIColor clearColor].CGColor;
    self.boxes.lineWidth = 1.5;
    self.boxes.strokeColor = RAVEN_RED.CGColor;

    self.lines  = [CAShapeLayer layer];
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
    UIWindowScene *scene = nil;
    for (UIScene *s in [UIApplication sharedApplication].connectedScenes) {
        if ([s isKindOfClass:[UIWindowScene class]]) {
            if (s.activationState == UISceneActivationStateForegroundActive ||
                s.activationState == UISceneActivationStateForegroundInactive) {
                scene = (UIWindowScene *)s; break;
            }
        }
    }
    if (scene) {
        self.window.windowScene = scene;
        self.window.hidden = NO;
    }
}

- (void)begin { self.boxes.path = NULL; self.lines.path = NULL; self.labels.string = @""; }
- (void)end   {}

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

- (void)drawText:(NSString*)s at:(CGPoint)p color:(UIColor*)c {
    NSMutableString *all = [NSMutableString stringWithString:self.labels.string ?: @""];
    [all appendFormat:@"\n%@", s];
    self.labels.string = all;
}

- (void)render {
    // Called by the menu when Engine is on.
    // Full implementation depends on the offsets in GameData.h.
}
@end
""")

w("Src/Aimbot.h", r"""
#ifndef RAVEN_AIMBOT_H
#define RAVEN_AIMBOT_H
#include "Common.h"

namespace RavenAimbot {
    void setEnabled(bool on);
    void setBone(int boneIdx);      // 11 = head, 12 = neck, 20 = chest
    void setSmooth(float amount);    // 1.0 = instant, higher = smoother
    void setFov(float radiusPx);     // pixels on screen

    void tick();
}
#endif
""")

w("Src/Aimbot.mm", r"""
#import "Aimbot.h"
#import "GameData.h"
#import "IL2CPP.h"

namespace RavenAimbot {

static bool g_on = false;
static int  g_bone = GameData::Bone::Head;
static float g_smooth = 3.0f;
static float g_fov = 300.0f;

void setEnabled(bool on) { g_on = on; }
void setBone(int b)      { g_bone = b; }
void setSmooth(float s)  { g_smooth = s > 0 ? s : 1.0f; }
void setFov(float r)     { g_fov = r; }

void tick() {
    if (!g_on) return;
    // Called every frame by the menu tick.
    // Full implementation needs: local player pointer, player list, camera,
    // and bone world positions. All read via GameData offsets.
}
}
""")

w("Src/Menu.h", r"""
#ifndef RAVEN_MENU_H
#define RAVEN_MENU_H
#import <UIKit/UIKit.h>
#import <QuartzCore/QuartzCore.h>

@interface RavenMenu : NSObject
+ (instancetype)shared;
- (void)start;
- (void)setVisible:(BOOL)v;
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

// ============================================================
// Helpers
// ============================================================
static UIImage* decodeB64(const char* b64) {
    if (!b64 || !*b64) return nil;
    NSString* s = [NSString stringWithUTF8String:b64];
    NSData* d = [[NSData alloc] initWithBase64EncodedString:s
                                                    options:NSDataBase64DecodingIgnoreUnknownCharacters];
    return d ? [UIImage imageWithData:d] : nil;
}

@interface RavenMenu () <UIGestureRecognizerDelegate>
@property (nonatomic, strong) UIWindow *window;
@property (nonatomic, strong) UIView   *ball;
@property (nonatomic, strong) UIView   *panel;
@property (nonatomic, assign) BOOL      panelOpen;
@property (nonatomic, assign) BOOL      engineOn;
@property (nonatomic, strong) NSTimer  *tickTimer;
@property (nonatomic, assign) CGPoint   ballStart;
@property (nonatomic, assign) CGPoint   panelStart;
@end

@implementation RavenMenu

+ (instancetype)shared {
    static RavenMenu *s; static dispatch_once_t once;
    dispatch_once(&once, ^{ s = [RavenMenu new]; });
    return s;
}

- (void)start {
    if (self.window) return;
    [[RavenESP shared] attach];

    self.window = [[UIWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
    self.window.windowLevel = UIWindowLevelAlert + 100;
    self.window.backgroundColor = [UIColor clearColor];
    self.window.rootViewController = [UIViewController new];
    self.window.rootViewController.view.backgroundColor = [UIColor clearColor];
    self.window.hidden = NO;
    [self attachToScene];

    [self buildBall];
    [self buildPanel];

    [self.window addSubview:self.ball];
    [self.window addSubview:self.panel];
    self.panel.hidden = YES;

    // 60 Hz tick that runs aimbot + ESP refresh
    self.tickTimer = [NSTimer scheduledTimerWithTimeInterval:1.0/60.0
                                                      target:self
                                                    selector:@selector(onTick)
                                                    userInfo:nil
                                                     repeats:YES];

    RAVEN_LOG("menu started");
}

- (void)attachToScene {
    for (UIScene *s in [UIApplication sharedApplication].connectedScenes) {
        if ([s isKindOfClass:[UIWindowScene class]]) {
            if (s.activationState == UISceneActivationStateForegroundActive ||
                s.activationState == UISceneActivationStateForegroundInactive) {
                self.window.windowScene = (UIWindowScene *)s;
                break;
            }
        }
    }
}

- (void)setVisible:(BOOL)v { self.window.hidden = !v; }

// ============================================================
// Ball
// ============================================================
- (void)buildBall {
    CGFloat size = 56.0;
    CGFloat x = [UIScreen mainScreen].bounds.size.width - size - 20;
    CGFloat y = 120.0;
    self.ball = [[UIView alloc] initWithFrame:CGRectMake(x, y, size, size)];
    self.ball.backgroundColor = RAVEN_BG;
    self.ball.layer.cornerRadius = size / 2.0;
    self.ball.layer.borderWidth = 2.0;
    self.ball.layer.borderColor = RAVEN_RED.CGColor;
    self.ball.layer.shadowColor = RAVEN_RED.CGColor;
    self.ball.layer.shadowOpacity = 0.8;
    self.ball.layer.shadowRadius = 10;
    self.ball.layer.shadowOffset = CGSizeZero;
    self.ball.userInteractionEnabled = YES;

    UIImage *ballLogo = decodeB64(kBallLogoB64);
    if (ballLogo) {
        UIImageView *iv = [[UIImageView alloc] initWithFrame:self.ball.bounds];
        iv.image = ballLogo;
        iv.contentMode = UIViewContentModeScaleAspectFill;
        iv.layer.cornerRadius = size / 2.0;
        iv.clipsToBounds = YES;
        [self.ball addSubview:iv];
    } else {
        UILabel *l = [[UILabel alloc] initWithFrame:self.ball.bounds];
        l.text = @"R";
        l.textAlignment = NSTextAlignmentCenter;
        l.font = [UIFont fontWithName:@"AvenirNext-Bold" size:26] ?: [UIFont boldSystemFontOfSize:26];
        l.textColor = RAVEN_RED;
        [self.ball addSubview:l];
    }

    // tap toggles panel; drag moves ball
    UITapGestureRecognizer *tap = [[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(togglePanel)];
    UIPanGestureRecognizer *pan = [[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(dragBall:)];
    [self.ball addGestureRecognizer:tap];
    [self.ball addGestureRecognizer:pan];
}

- (void)togglePanel {
    self.panelOpen = !self.panelOpen;
    self.panel.hidden = !self.panelOpen;
}

- (void)dragBall:(UIPanGestureRecognizer*)g {
    CGPoint t = [g translationInView:self.window];
    self.ball.center = CGPointMake(self.ball.center.x + t.x, self.ball.center.y + t.y);
    [g setTranslation:CGPointZero inView:self.window];
}

// ============================================================
// Panel
// ============================================================
- (UIView*)makeRowWithLabel:(NSString*)text control:(UIView*)ctrl {
    UIView *row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 260, 34)];
    UILabel *l = [[UILabel alloc] initWithFrame:CGRectMake(0, 0, 140, 34)];
    l.text = text;
    l.textColor = RAVEN_SILVER;
    l.font = [UIFont systemFontOfSize:13 weight:UIFontWeightMedium];
    ctrl.frame = CGRectMake(150, 4, 110, 26);
    [row addSubview:l];
    [row addSubview:ctrl];
    return row;
}

- (UISwitch*)makeSwitch:(SEL)action on:(BOOL)on {
    UISwitch *s = [[UISwitch alloc] init];
    s.onTintColor = RAVEN_RED;
    s.on = on;
    [s addTarget:self action:action forControlEvents:UIControlEventValueChanged];
    return s;
}

- (UISlider*)makeSlider:(SEL)action min:(float)mn max:(float)mx val:(float)v {
    UISlider *s = [[UISlider alloc] init];
    s.minimumValue = mn;
    s.maximumValue = mx;
    s.value = v;
    s.minimumTrackTintColor = RAVEN_RED;
    s.maximumTrackTintColor = RAVEN_DARK;
    [s addTarget:self action:action forControlEvents:UIControlEventValueChanged];
    return s;
}

- (void)buildPanel {
    CGFloat W = 280, H = 460;
    CGFloat x = [UIScreen mainScreen].bounds.size.width - W - 12;
    CGFloat y = 190;
    self.panel = [[UIView alloc] initWithFrame:CGRectMake(x, y, W, H)];
    self.panel.backgroundColor = RAVEN_BG;
    self.panel.layer.cornerRadius = 14;
    self.panel.layer.borderWidth = 1;
    self.panel.layer.borderColor = [RAVEN_RED colorWithAlphaComponent:0.5].CGColor;
    self.panel.layer.shadowColor = [UIColor blackColor].CGColor;
    self.panel.layer.shadowOpacity = 0.6;
    self.panel.layer.shadowRadius = 16;
    self.panel.layer.shadowOffset = CGSizeMake(0, 6);

    // Header with logo
    UIView *header = [[UIView alloc] initWithFrame:CGRectMake(0, 0, W, 80)];
    header.backgroundColor = [RAVEN_DARK colorWithAlphaComponent:0.9];
    header.layer.cornerRadius = 14;
    header.layer.maskedCorners = kCALayerMinXMinYCorner | kCALayerMaxXMinYCorner;

    UIImage *headerLogo = decodeB64(kHeaderLogoB64);
    if (headerLogo) {
        UIImageView *hv = [[UIImageView alloc] initWithFrame:CGRectMake(10, 10, W-20, 48)];
        hv.image = headerLogo;
        hv.contentMode = UIViewContentModeScaleAspectFit;
        [header addSubview:hv];
    } else {
        UILabel *t = [[UILabel alloc] initWithFrame:CGRectMake(0, 12, W, 28)];
        t.text = @"RAVEN";
        t.textAlignment = NSTextAlignmentCenter;
        t.textColor = RAVEN_RED;
        t.font = [UIFont fontWithName:@"AvenirNext-Bold" size:22] ?: [UIFont boldSystemFontOfSize:22];
        [header addSubview:t];
    }
    UILabel *ver = [[UILabel alloc] initWithFrame:CGRectMake(0, 54, W, 18)];
    ver.text = @"v1  ·  @Kremityss";
    ver.textAlignment = NSTextAlignmentCenter;
    ver.textColor = RAVEN_SILVER;
    ver.font = [UIFont systemFontOfSize:10 weight:UIFontWeightLight];
    [header addSubview:ver];

    [self.panel addSubview:header];

    // Close button
    UIButton *close = [UIButton buttonWithType:UIButtonTypeSystem];
    close.frame = CGRectMake(W - 44, 10, 34, 34);
    [close setTitle:@"✕" forState:UIControlStateNormal];
    [close setTitleColor:RAVEN_RED forState:UIControlStateNormal];
    close.titleLabel.font = [UIFont systemFontOfSize:20 weight:UIFontWeightBold];
    [close addTarget:self action:@selector(togglePanel) forControlEvents:UIControlEventTouchUpInside];
    [self.panel addSubview:close];

    // Scrollable content
    UIScrollView *sv = [[UIScrollView alloc] initWithFrame:CGRectMake(10, 90, W - 20, H - 100)];
    sv.showsVerticalScrollIndicator = NO;

    NSArray *rows = @[
        [self makeRowWithLabel:@"Engine"      control:[self makeSwitch:@selector(onEngine) on:NO]],
        [self makeRowWithLabel:@"ESP"         control:[self makeSwitch:@selector(onESP) on:YES]],
        [self makeRowWithLabel:@"Aimbot"      control:[self makeSwitch:@selector(onAim) on:NO]],
        [self makeRowWithLabel:@"Visibility"  control:[self makeSwitch:@selector(onVis) on:YES]],
        [self makeRowWithLabel:@"FOV"         control:[self makeSlider:@selector(onFOV) min:50 max:800 val:300]],
        [self makeRowWithLabel:@"Smooth"      control:[self makeSlider:@selector(onSmooth) min:1 max:10 val:3]],
        [self makeRowWithLabel:@"Aim Power"   control:[self makeSlider:@selector(onPower) min:0.1 max:1.0 val:0.6]],
        [self makeRowWithLabel:@"Box Color"   control:[self makeSwitch:@selector(onColor) on:NO]],
    ];

    CGFloat yOff = 0;
    for (UIView *row in rows) {
        row.frame = CGRectMake(0, yOff, W - 20, 34);
        [sv addSubview:row];
        yOff += 40;
    }
    sv.contentSize = CGSizeMake(W - 20, yOff + 20);
    [self.panel addSubview:sv];

    // Drag panel via header
    UIPanGestureRecognizer *pp = [[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(dragPanel:)];
    [header addGestureRecognizer:pp];
}

- (void)dragPanel:(UIPanGestureRecognizer*)g {
    CGPoint t = [g translationInView:self.window];
    self.panel.center = CGPointMake(self.panel.center.x + t.x, self.panel.center.y + t.y);
    [g setTranslation:CGPointZero inView:self.window];
}

// ============================================================
// Switch / slider actions
// ============================================================
- (void)onEngine:(UISwitch*)s {
    self.engineOn = s.on;
    if (s.on) { [[RavenESP shared] begin]; }
    RAVEN_LOG("engine %d", s.on);
}
- (void)onESP:(UISwitch*)s    { RAVEN_LOG("esp %d", s.on); }
- (void)onAim:(UISwitch*)s    { RavenAimbot::setEnabled(s.on); }
- (void)onVis:(UISwitch*)s    { RAVEN_LOG("vis %d", s.on); }
- (void)onFOV:(UISlider*)s    { RavenAimbot::setFov(s.value); }
- (void)onSmooth:(UISlider*)s { RavenAimbot::setSmooth(s.value); }
- (void)onPower:(UISlider*)s  { RAVEN_LOG("power %.2f", s.value); }
- (void)onColor:(UISwitch*)s  { RAVEN_LOG("color %d", s.on); }

- (void)onTick {
    if (!self.engineOn) return;
    [[RavenESP shared] begin];
    [[RavenESP shared] render];
    RavenAimbot::tick();
}

@end
""")

print("done — Raven v1 project written")
