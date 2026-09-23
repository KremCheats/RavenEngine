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

#include <cstdint>
#include <cstddef>

#import <Foundation/Foundation.h>
#import <os/log.h>

#define RAVEN_LOG(fmt, ...) os_log(OS_LOG_DEFAULT, "[raven] " fmt, ##__VA_ARGS__)

struct Vec3 { float x, y, z; };
struct Matrix4x4 { float m[16]; };

#define RAVEN_RED    [UIColor colorWithRed:0.769 green:0.118 blue:0.118 alpha:1.0]
#define RAVEN_RED_DK [UIColor colorWithRed:0.400 green:0.060 blue:0.060 alpha:1.0]
#define RAVEN_SILVER [UIColor colorWithRed:0.910 green:0.910 blue:0.910 alpha:1.0]
#define RAVEN_GREY   [UIColor colorWithRed:0.550 green:0.550 blue:0.580 alpha:1.0]
#define RAVEN_BG     [UIColor colorWithRed:0.039 green:0.039 blue:0.039 alpha:0.98]
#define RAVEN_DARK   [UIColor colorWithRed:0.075 green:0.075 blue:0.085 alpha:1.0]
#define RAVEN_CARD   [UIColor colorWithRed:0.110 green:0.110 blue:0.120 alpha:0.9]

#endif
""")

w("Src/GameData.h", r"""
#ifndef RAVEN_GAMEDATA_H
#define RAVEN_GAMEDATA_H

#include <cstdint>

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
        constexpr uint32_t Health      = 0x0;
        constexpr uint32_t Armor       = 0x0;
        constexpr uint32_t Position    = 0x0;
        constexpr uint32_t TeamId      = 0x0;
        constexpr uint32_t IsVisible   = 0x0;
        constexpr uint32_t IsLocal     = 0x0;

        constexpr uint32_t ListCount   = 0x18;
        constexpr uint32_t ListItems   = 0x10;
        constexpr uint32_t ArrayData   = 0x20;

        constexpr uint32_t ViewMatrix  = 0x0;
        constexpr uint32_t ProjMatrix  = 0x0;
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

static const char* kBallLogoURL   = "https://i.imgur.com/MQG4stU.png";
static const char* kHeaderLogoURL = "https://i.imgur.com/Cnzjdjh.png";
static const char* kSidebarArtURL = "https://i.imgur.com/80o5CRE.png";

#endif
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
                self.window.hidden = NO;
                return;
            }
        }
    }
}

- (void)begin {
    self.boxes.path = NULL;
    self.lines.path = NULL;
}

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

- (void)drawText:(NSString*)s at:(CGPoint)p color:(UIColor*)c {
}

- (void)render {
}

@end
""")

w("Src/Aimbot.h", r"""
#ifndef RAVEN_AIMBOT_H
#define RAVEN_AIMBOT_H
#include "Common.h"

namespace RavenAimbot {
    void setEnabled(bool on);
    void setBone(int boneIdx);
    void setSmooth(float amount);
    void setFov(float radiusPx);
    void setKey(int keyCode);
    void setSilent(bool on);
    void setVisCheck(bool on);
    void setPrediction(bool on);
    void tick();
}
#endif
""")

w("Src/Aimbot.mm", r"""
#import "Aimbot.h"
#import "GameData.h"
#import "IL2CPP.h"

namespace RavenAimbot {

static bool  g_on        = false;
static int   g_bone      = GameData::Bone::Head;
static float g_smooth    = 5.0f;
static float g_fov       = 120.0f;
static int   g_key       = 0;
static bool  g_silent    = false;
static bool  g_vis       = true;
static bool  g_pred      = true;

void setEnabled(bool on) { g_on = on; }
void setBone(int b)      { g_bone = b; }
void setSmooth(float s)  { g_smooth = s > 0 ? s : 1.0f; }
void setFov(float r)     { g_fov = r; }
void setKey(int k)       { g_key = k; }
void setSilent(bool on)  { g_silent = on; }
void setVisCheck(bool on){ g_vis = on; }
void setPrediction(bool on){ g_pred = on; }

void tick() {
    if (!g_on) return;
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

// ==================================================================
// image loading — URL based, with memory + disk cache
// ==================================================================
static NSCache* g_imgCache = nil;

static UIImage* loadLogoURL(const char* url) {
    if (!url || !*url) return nil;
    if (!g_imgCache) g_imgCache = [[NSCache alloc] init];

    NSString* key = [NSString stringWithUTF8String:url];
    UIImage* cached = [g_imgCache objectForKey:key];
    if (cached) return cached;

    NSString* dir = [NSSearchPathForDirectoriesInDomains(NSCachesDirectory, NSUserDomainMask, YES) firstObject];
    NSString* hash = [NSString stringWithFormat:@"%lu", (unsigned long)key.hash];
    NSString* path = [dir stringByAppendingPathComponent:[hash stringByAppendingString:@".img"]];
    NSData* data = [NSData dataWithContentsOfFile:path];

    if (!data) {
        NSURL* u = [NSURL URLWithString:key];
        if (!u) return nil;
        data = [NSData dataWithContentsOfURL:u];
        if (data) [data writeToFile:path atomically:YES];
    }
    if (!data) return nil;

    UIImage* img = [UIImage imageWithData:data];
    if (img) [g_imgCache setObject:img forKey:key];
    return img;
}

static UILabel* mkLabel(NSString* text, CGFloat size, UIColor* color, BOOL bold) {
    UILabel* l = [UILabel new];
    l.text = text;
    l.textColor = color;
    l.font = bold ? [UIFont systemFontOfSize:size weight:UIFontWeightBold]
                  : [UIFont systemFontOfSize:size weight:UIFontWeightMedium];
    l.numberOfLines = 1;
    return l;
}

// ==================================================================
@interface RavenMenu ()
@property (nonatomic, strong) UIWindow *window;
@property (nonatomic, strong) UIView   *panel;
@property (nonatomic, strong) UIView   *headerView;
@property (nonatomic, strong) UIView   *sidebarView;
@property (nonatomic, strong) UIView   *contentView;
@property (nonatomic, strong) UIView   *footerView;
@property (nonatomic, strong) UIView   *ball;
@property (nonatomic, strong) NSMutableArray *tabButtons;
@property (nonatomic, strong) NSMutableDictionary *tabViews;
@property (nonatomic, assign) NSInteger activeTab;
@property (nonatomic, strong) NSTimer *tickTimer;
@property (nonatomic, assign) BOOL panelOpen;
@property (nonatomic, assign) BOOL engineOn;
@property (nonatomic, assign) BOOL aimOn;
@property (nonatomic, assign) BOOL espOn;
@property (nonatomic, assign) BOOL visOn;
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

    self.tabButtons = [NSMutableArray array];
    self.tabViews = [NSMutableDictionary dictionary];
    self.activeTab = 0;

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

    self.tickTimer = [NSTimer scheduledTimerWithTimeInterval:1.0/30.0
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
                return;
            }
        }
    }
}

- (void)setVisible:(BOOL)v { self.window.hidden = !v; }

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

    UIImage *ballLogo = loadLogoURL(kBallLogoURL);
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
        l.font = [UIFont boldSystemFontOfSize:26];
        l.textColor = RAVEN_RED;
        [self.ball addSubview:l];
    }

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

- (void)buildPanel {
    CGRect scr = [UIScreen mainScreen].bounds;
    CGFloat margin = 8;
    CGFloat W = scr.size.width - margin*2;
    CGFloat H = scr.size.height - margin*2;

    self.panel = [[UIView alloc] initWithFrame:CGRectMake(margin, margin, W, H)];
    self.panel.backgroundColor = RAVEN_BG;
    self.panel.layer.cornerRadius = 14;
    self.panel.layer.borderWidth = 1;
    self.panel.layer.borderColor = [RAVEN_RED colorWithAlphaComponent:0.6].CGColor;
    self.panel.layer.shadowColor = RAVEN_RED.CGColor;
    self.panel.layer.shadowOpacity = 0.4;
    self.panel.layer.shadowRadius = 20;
    self.panel.layer.shadowOffset = CGSizeMake(0, 6);

    CGFloat headerH = 96;
    CGFloat footerH = 30;
    CGFloat sidebarW = 120;

    [self buildHeader:CGRectMake(0, 0, W, headerH)];
    [self buildSidebar:CGRectMake(0, headerH, sidebarW, H - headerH - footerH)];
    [self buildContent:CGRectMake(sidebarW, headerH, W - sidebarW, H - headerH - footerH)];
    [self buildFooter:CGRectMake(0, H - footerH, W, footerH)];

    [self.panel addSubview:self.headerView];
    [self.panel addSubview:self.sidebarView];
    [self.panel addSubview:self.contentView];
    [self.panel addSubview:self.footerView];

    [self selectTab:0];
}

- (void)buildHeader:(CGRect)r {
    self.headerView = [[UIView alloc] initWithFrame:r];
    self.headerView.backgroundColor = RAVEN_DARK;
    self.headerView.layer.cornerRadius = 14;
    self.headerView.layer.maskedCorners = kCALayerMinXMinYCorner | kCALayerMaxXMinYCorner;
    self.headerView.layer.borderWidth = 1;
    self.headerView.layer.borderColor = [RAVEN_RED colorWithAlphaComponent:0.4].CGColor;

    UIImage *logo = loadLogoURL(kHeaderLogoURL);
    if (logo) {
        UIImageView *iv = [[UIImageView alloc] initWithFrame:CGRectMake(6, 6, r.size.width - 12, r.size.height - 12)];
        iv.image = logo;
        iv.contentMode = UIViewContentModeScaleAspectFit;
        [self.headerView addSubview:iv];
    } else {
        UILabel *title = mkLabel(@"RAVEN", 30, RAVEN_RED, YES);
        title.frame = CGRectMake(16, 8, 200, 36);
        [self.headerView addSubview:title];
        UILabel *byline = mkLabel(@"BY KREMCHEATS   DEV: KREMIT YSS", 9, RAVEN_SILVER, NO);
        byline.frame = CGRectMake(18, 44, 200, 14);
        [self.headerView addSubview:byline];
    }

    // close button (always overlays logo)
    UIButton *close = [UIButton buttonWithType:UIButtonTypeSystem];
    close.frame = CGRectMake(r.size.width - 42, 6, 36, 30);
    [close setTitle:@"X" forState:UIControlStateNormal];
    [close setTitleColor:RAVEN_RED forState:UIControlStateNormal];
    close.titleLabel.font = [UIFont boldSystemFontOfSize:18];
    close.backgroundColor = [UIColor colorWithWhite:0 alpha:0.45];
    close.layer.cornerRadius = 6;
    [close addTarget:self action:@selector(togglePanel) forControlEvents:UIControlEventTouchUpInside];
    [self.headerView addSubview:close];
}

- (NSArray*)tabDefs {
    return @[
        @{@"title":@"AIMBOT",   @"icon":@"scope"},
        @{@"title":@"ESP",      @"icon":@"eye.fill"},
        @{@"title":@"VISUALS",  @"icon":@"sparkles.tv.fill"},
        @{@"title":@"MISC",     @"icon":@"gearshape.2.fill"},
        @{@"title":@"PLAYERS",  @"icon":@"person.2.fill"},
        @{@"title":@"CONFIG",   @"icon":@"doc.text.fill"},
        @{@"title":@"SETTINGS", @"icon":@"gear"},
    ];
}

- (void)buildSidebar:(CGRect)r {
    self.sidebarView = [[UIView alloc] initWithFrame:r];
    self.sidebarView.backgroundColor = [RAVEN_DARK colorWithAlphaComponent:0.5];
    self.sidebarView.clipsToBounds = YES;

    // art first (behind everything)
    UIImage *art = loadLogoURL(kSidebarArtURL);
    if (art) {
        UIImageView *iv = [[UIImageView alloc] initWithFrame:CGRectMake(0, 0, r.size.width, r.size.height)];
        iv.image = art;
        iv.contentMode = UIViewContentModeScaleAspectFill;
        iv.alpha = 0.18;
        iv.clipsToBounds = YES;
        [self.sidebarView addSubview:iv];
    }

    NSArray *defs = [self tabDefs];
    CGFloat y = 12;
    CGFloat h = 48;

    for (NSInteger i = 0; i < defs.count; i++) {
        NSDictionary *d = defs[i];
        UIButton *btn = [UIButton buttonWithType:UIButtonTypeCustom];
        btn.frame = CGRectMake(8, y, r.size.width - 16, h);
        btn.tag = i;
        btn.backgroundColor = [UIColor clearColor];
        btn.layer.cornerRadius = 8;
        [btn addTarget:self action:@selector(onTabTap:) forControlEvents:UIControlEventTouchUpInside];

        UIImageView *icon = nil;
        if (@available(iOS 13.0, *)) {
            UIImage *img = [UIImage systemImageNamed:d[@"icon"]];
            icon = [[UIImageView alloc] initWithImage:img];
            icon.tintColor = RAVEN_RED;
            icon.frame = CGRectMake(8, h/2 - 10, 20, 20);
        }
        if (icon) [btn addSubview:icon];

        UILabel *label = mkLabel(d[@"title"], 12, RAVEN_SILVER, YES);
        label.frame = CGRectMake(icon ? 36 : 12, 0, btn.frame.size.width - 44, h);
        [btn addSubview:label];

        [self.sidebarView addSubview:btn];
        [self.tabButtons addObject:btn];
        y += h + 4;
    }

    UILabel *motto = mkLabel(@"\"SEE MORE\nBE BETTER\"", 9, RAVEN_RED, NO);
    motto.numberOfLines = 2;
    motto.textAlignment = NSTextAlignmentCenter;
    motto.frame = CGRectMake(0, r.size.height - 40, r.size.width, 30);
    [self.sidebarView addSubview:motto];
}

- (void)onTabTap:(UIButton*)b {
    [self selectTab:b.tag];
}

- (void)selectTab:(NSInteger)idx {
    self.activeTab = idx;
    for (NSInteger i = 0; i < self.tabButtons.count; i++) {
        UIButton *b = self.tabButtons[i];
        b.backgroundColor = (i == idx) ? [RAVEN_RED colorWithAlphaComponent:0.18] : [UIColor clearColor];
    }
    for (UIView *v in self.contentView.subviews) [v removeFromSuperview];

    NSArray *defs = [self tabDefs];
    NSString *key = defs[idx][@"title"];
    UIView *content = self.tabViews[key];
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
}

- (UIView*)buildTabContent:(NSString*)tab {
    UIScrollView *sv = [[UIScrollView alloc] initWithFrame:self.contentView.bounds];
    sv.backgroundColor = [UIColor clearColor];
    sv.showsVerticalScrollIndicator = NO;

    CGFloat pad = 10;
    CGFloat y = pad;
    CGFloat W = sv.bounds.size.width - pad*2;
    if (W < 100) W = 260;

    NSArray *rows = [self rowsForTab:tab];
    for (UIView *row in rows) {
        row.frame = CGRectMake(pad, y, W, row.frame.size.height);
        [sv addSubview:row];
        y += row.frame.size.height + 6;
    }
    sv.contentSize = CGSizeMake(W, y + 20);
    return sv;
}

- (NSArray*)rowsForTab:(NSString*)tab {
    if ([tab isEqualToString:@"AIMBOT"]) {
        return @[
            [self switchRow:@"Enable Aimbot" sel:@selector(onAimToggle:) on:NO],
            [self dropdownRow:@"Aim Key" value:@"LMB"],
            [self sliderRow:@"Aim FOV" min:0 max:360 val:120 sel:@selector(onAimFov:)],
            [self sliderRow:@"Smoothness" min:1 max:30 val:5 sel:@selector(onAimSmooth:)],
            [self dropdownRow:@"Target Bone" value:@"Head"],
            [self switchRow:@"Prediction" sel:@selector(onAimPred:) on:YES],
            [self switchRow:@"Visibility Check" sel:@selector(onAimVis:) on:YES],
            [self switchRow:@"Ignore Knocked" sel:@selector(onNoop:) on:NO],
            [self switchRow:@"Silent Aim" sel:@selector(onAimSilent:) on:NO],
        ];
    }
    if ([tab isEqualToString:@"ESP"]) {
        return @[
            [self switchRow:@"Enable ESP" sel:@selector(onEspToggle:) on:YES],
            [self switchRow:@"Box ESP" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Skeleton" sel:@selector(onNoop:) on:NO],
            [self switchRow:@"Player Names" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Distance" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Health Bar" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Weapon ESP" sel:@selector(onNoop:) on:NO],
            [self switchRow:@"Snaplines" sel:@selector(onNoop:) on:NO],
            [self switchRow:@"Visible Only" sel:@selector(onNoop:) on:YES],
        ];
    }
    if ([tab isEqualToString:@"VISUALS"]) {
        return @[
            [self switchRow:@"No Recoil" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"No Spread" sel:@selector(onNoop:) on:YES],
            [self sliderRow:@"FOV Changer" min:60 max:140 val:110 sel:@selector(onNoopSlider:)],
            [self switchRow:@"Remove Fog" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Better Textures" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Night Mode" sel:@selector(onNoop:) on:YES],
            [self dropdownRow:@"Crosshair" value:@"Dot"],
            [self sliderRow:@"Brightness" min:0 max:200 val:100 sel:@selector(onNoopSlider:)],
        ];
    }
    if ([tab isEqualToString:@"MISC"]) {
        return @[
            [self switchRow:@"Bunny Hop" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Auto Strafe" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Rapid Fire" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"No Flash" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"No Smoke" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Fast Reload" sel:@selector(onNoop:) on:YES],
            [self switchRow:@"Unlock All" sel:@selector(onNoop:) on:NO],
        ];
    }
    if ([tab isEqualToString:@"PLAYERS"]) {
        NSMutableArray *rows = [NSMutableArray array];
        NSArray *names = @[@"Kremityss 12m", @"Devoo 28m", @"VAMP 41m", @"797 BUDDA 63m",
                           @"Player123 87m", @"User456 104m", @"Enemy 132m", @"Target 148m"];
        for (NSString *n in names) [rows addObject:[self listRow:n]];
        return rows;
    }
    if ([tab isEqualToString:@"CONFIG"]) {
        return @[
            [self dropdownRow:@"Preset" value:@"Legit"],
            [self buttonRow:@"Load Config" sel:@selector(onNoopTap:)],
            [self buttonRow:@"Save Config" sel:@selector(onNoopTap:)],
            [self buttonRow:@"Delete Config" sel:@selector(onNoopTap:)],
        ];
    }
    if ([tab isEqualToString:@"SETTINGS"]) {
        return @[
            [self infoRow:@"Version" value:@"1.0.0"],
            [self infoRow:@"Developer" value:@"Kremityss"],
            [self infoRow:@"Brand" value:@"KREMCHEATS"],
            [self switchRow:@"Stream Proof" sel:@selector(onNoop:) on:NO],
            [self switchRow:@"Panic Key" sel:@selector(onNoop:) on:YES],
        ];
    }
    return @[];
}

- (UIView*)baseRow {
    UIView *row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 280, 44)];
    row.backgroundColor = RAVEN_CARD;
    row.layer.cornerRadius = 8;
    row.layer.borderWidth = 1;
    row.layer.borderColor = [RAVEN_RED colorWithAlphaComponent:0.18].CGColor;
    return row;
}

- (UIView*)switchRow:(NSString*)title sel:(SEL)sel on:(BOOL)on {
    UIView *row = [self baseRow];
    UILabel *l = mkLabel(title, 13, RAVEN_SILVER, NO);
    l.frame = CGRectMake(14, 0, row.frame.size.width - 90, row.frame.size.height);
    [row addSubview:l];

    UISwitch *sw = [[UISwitch alloc] init];
    sw.onTintColor = RAVEN_RED;
    sw.on = on;
    sw.transform = CGAffineTransformMakeScale(0.75, 0.75);
    sw.center = CGPointMake(row.frame.size.width - 40, row.frame.size.height / 2);
    [sw addTarget:self action:sel forControlEvents:UIControlEventValueChanged];
    [row addSubview:sw];
    return row;
}

- (UIView*)sliderRow:(NSString*)title min:(float)mn max:(float)mx val:(float)v sel:(SEL)sel {
    UIView *row = [self baseRow];
    row.frame = CGRectMake(0, 0, 280, 54);

    UILabel *l = mkLabel(title, 13, RAVEN_SILVER, NO);
    l.frame = CGRectMake(14, 4, 160, 20);
    [row addSubview:l];

    UILabel *val = mkLabel([NSString stringWithFormat:@"%.0f", v], 12, RAVEN_RED, YES);
    val.textAlignment = NSTextAlignmentRight;
    val.frame = CGRectMake(row.frame.size.width - 60, 4, 46, 20);
    [row addSubview:val];

    UISlider *sl = [[UISlider alloc] init];
    sl.frame = CGRectMake(14, 28, row.frame.size.width - 28, 22);
    sl.minimumValue = mn;
    sl.maximumValue = mx;
    sl.value = v;
    sl.minimumTrackTintColor = RAVEN_RED;
    sl.maximumTrackTintColor = [UIColor colorWithWhite:0.25 alpha:1.0];
    sl.thumbTintColor = [UIColor whiteColor];
    [sl addTarget:self action:sel forControlEvents:UIControlEventValueChanged];
    [row addSubview:sl];
    return row;
}

- (UIView*)dropdownRow:(NSString*)title value:(NSString*)val {
    UIView *row = [self baseRow];
    UILabel *l = mkLabel(title, 13, RAVEN_SILVER, NO);
    l.frame = CGRectMake(14, 0, 140, row.frame.size.height);
    [row addSubview:l];

    UIView *pill = [[UIView alloc] initWithFrame:CGRectMake(row.frame.size.width - 120, 8, 106, 28)];
    pill.backgroundColor = [UIColor colorWithWhite:0.18 alpha:1.0];
    pill.layer.cornerRadius = 6;
    pill.layer.borderWidth = 1;
    pill.layer.borderColor = [RAVEN_RED colorWithAlphaComponent:0.3].CGColor;
    [row addSubview:pill];

    UILabel *v = mkLabel(val, 12, RAVEN_SILVER, NO);
    v.textAlignment = NSTextAlignmentCenter;
    v.frame = pill.bounds;
    [pill addSubview:v];
    return row;
}

- (UIView*)buttonRow:(NSString*)title sel:(SEL)sel {
    UIView *row = [self baseRow];
    UIButton *b = [UIButton buttonWithType:UIButtonTypeCustom];
    b.frame = row.bounds;
    [b setTitle:title forState:UIControlStateNormal];
    [b setTitleColor:RAVEN_SILVER forState:UIControlStateNormal];
    b.titleLabel.font = [UIFont systemFontOfSize:13 weight:UIFontWeightMedium];
    [b addTarget:self action:sel forControlEvents:UIControlEventTouchUpInside];
    [row addSubview:b];
    return row;
}

- (UIView*)infoRow:(NSString*)title value:(NSString*)val {
    UIView *row = [self baseRow];
    UILabel *l = mkLabel(title, 13, RAVEN_SILVER, NO);
    l.frame = CGRectMake(14, 0, 140, row.frame.size.height);
    [row addSubview:l];
    UILabel *v = mkLabel(val, 12, RAVEN_RED, YES);
    v.textAlignment = NSTextAlignmentRight;
    v.frame = CGRectMake(row.frame.size.width - 160, 0, 146, row.frame.size.height);
    [row addSubview:v];
    return row;
}

- (UIView*)listRow:(NSString*)text {
    UIView *row = [self baseRow];
    row.frame = CGRectMake(0, 0, 280, 36);
    UILabel *l = mkLabel(text, 12, RAVEN_SILVER, NO);
    l.frame = CGRectMake(14, 0, row.frame.size.width - 28, row.frame.size.height);
    [row addSubview:l];
    return row;
}

- (void)buildFooter:(CGRect)r {
    self.footerView = [[UIView alloc] initWithFrame:r];
    self.footerView.backgroundColor = RAVEN_DARK;
    self.footerView.layer.cornerRadius = 14;
    self.footerView.layer.maskedCorners = kCALayerMinXMaxYCorner | kCALayerMaxXMaxYCorner;
    self.footerView.layer.borderWidth = 1;
    self.footerView.layer.borderColor = [RAVEN_RED colorWithAlphaComponent:0.3].CGColor;

    UIView *dot = [[UIView alloc] initWithFrame:CGRectMake(12, 11, 8, 8)];
    dot.backgroundColor = [UIColor colorWithRed:0.2 green:0.9 blue:0.3 alpha:1.0];
    dot.layer.cornerRadius = 4;
    [self.footerView addSubview:dot];

    UILabel *l = mkLabel(@"Game: Connected    Status: Undetected    FPS: 120    Latency: 12ms",
                         10, RAVEN_GREY, NO);
    l.frame = CGRectMake(26, 0, r.size.width - 220, r.size.height);
    [self.footerView addSubview:l];

    UILabel *r2 = mkLabel(@"RAVEN  |  KREMCHEATS  |  v1.0.0", 10, RAVEN_RED, YES);
    r2.textAlignment = NSTextAlignmentRight;
    r2.frame = CGRectMake(r.size.width - 220, 0, 208, r.size.height);
    [self.footerView addSubview:r2];
}

- (void)onAimToggle:(UISwitch*)s    { self.aimOn = s.on; RavenAimbot::setEnabled(s.on); }
- (void)onAimFov:(UISlider*)s       { RavenAimbot::setFov(s.value); }
- (void)onAimSmooth:(UISlider*)s    { RavenAimbot::setSmooth(s.value); }
- (void)onAimPred:(UISwitch*)s      { RavenAimbot::setPrediction(s.on); }
- (void)onAimVis:(UISwitch*)s       { RavenAimbot::setVisCheck(s.on); }
- (void)onAimSilent:(UISwitch*)s    { RavenAimbot::setSilent(s.on); }
- (void)onEspToggle:(UISwitch*)s    { self.espOn = s.on; }
- (void)onEngine:(UISwitch*)s       { self.engineOn = s.on; if (s.on) [[RavenESP shared] begin]; }
- (void)onNoop:(UISwitch*)s         { (void)s; }
- (void)onNoopSlider:(UISlider*)s   { (void)s; }
- (void)onNoopTap:(UIButton*)b      { (void)b; }

- (void)onTick {
    if (!self.engineOn) return;
    [[RavenESP shared] begin];
    [[RavenESP shared] render];
    RavenAimbot::tick();
}

@end
""")

print("done - Raven with imgur logo URLs")
