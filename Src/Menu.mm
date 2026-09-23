w("Src/Menu.mm", r"""
#import "Menu.h"
#import "Common.h"
#import "Logos.h"
#import "ESP.h"
#import "Aimbot.h"
#import "IL2CPP.h"
#import "Updater.h"

// ==================================================================
// palette
// ==================================================================
#define C_WIN     [UIColor colorWithRed:0.043 green:0.043 blue:0.055 alpha:0.97]
#define C_HEAD    [UIColor colorWithRed:0.051 green:0.051 blue:0.063 alpha:1.0]
#define C_SIDE    [UIColor colorWithRed:0.055 green:0.055 blue:0.071 alpha:1.0]
#define C_CARD    [UIColor colorWithRed:0.078 green:0.078 blue:0.090 alpha:1.0]
#define C_BORDER  [UIColor colorWithRed:0.157 green:0.157 blue:0.165 alpha:1.0]
#define C_RED     [UIColor colorWithRed:0.835 green:0.122 blue:0.157 alpha:1.0]
#define C_CRIMSON [UIColor colorWithRed:0.290 green:0.067 blue:0.086 alpha:1.0]
#define C_TEXT    [UIColor colorWithRed:0.949 green:0.949 blue:0.957 alpha:1.0]
#define C_SEC     [UIColor colorWithRed:0.573 green:0.573 blue:0.608 alpha:1.0]
#define C_MUTE    [UIColor colorWithRed:0.384 green:0.384 blue:0.420 alpha:1.0]

// reference design size
static const CGFloat kRefW      = 860;
static const CGFloat kRefH      = 500;
static const CGFloat kHeaderH   = 50;
static const CGFloat kFooterH   = 28;
static const CGFloat kSidebarW  = 165;
static const CGFloat kPad       = 18;
static const CGFloat kCardGap   = 12;
static const CGFloat kCardRad   = 8;
static const CGFloat kTabH      = 38;
static const CGFloat kRowH      = 26;
static const CGFloat kRowHBig   = 40;  // slider rows

// ==================================================================
// helpers
// ==================================================================
static NSCache* g_imgCache = nil;

static UIImage* loadLogoURL(const char* url) {
    if (!url || !*url) return nil;
    if (!g_imgCache) g_imgCache = [[NSCache alloc] init];
    NSString* key = [NSString stringWithUTF8String:url];
    UIImage* c = [g_imgCache objectForKey:key];
    if (c) return c;
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

static NSString* assetURL(const char* k, const char* fb) {
    std::string s = Updater::asset(std::string(k), std::string(fb ? fb : ""));
    return [NSString stringWithUTF8String:s.c_str()];
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
// custom toggle: 34x18
// ==================================================================
@implementation RVToggle {
    UIView* _track;
    UIView* _knob;
}
- (instancetype)init {
    if ((self = [super initWithFrame:CGRectMake(0,0,34,18)])) {
        self.userInteractionEnabled = YES;
        _track = [[UIView alloc] initWithFrame:CGRectMake(0,0,34,18)];
        _track.layer.cornerRadius = 9;
        _track.backgroundColor = [UIColor colorWithRed:0.204 green:0.204 blue:0.231 alpha:1.0];
        [self addSubview:_track];
        _knob = [[UIView alloc] initWithFrame:CGRectMake(2,2,14,14)];
        _knob.layer.cornerRadius = 7;
        _knob.backgroundColor = [UIColor colorWithWhite:0.94 alpha:1.0];
        [self addSubview:_knob];
        [self addGestureRecognizer:[[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(toggle)]];
    }
    return self;
}
- (void)toggle {
    self.on = !self.on;
    [self applyStateAnimated:YES];
    if (self.onChange) self.onChange(self.on);
}
- (void)setOn:(BOOL)on { [self setOn:on animated:NO]; }
- (void)setOn:(BOOL)on animated:(BOOL)animated {
    _on = on;
    [self applyStateAnimated:animated];
}
- (void)applyStateAnimated:(BOOL)animated {
    UIColor* bg = _on ? C_RED
                      : [UIColor colorWithRed:0.204 green:0.204 blue:0.231 alpha:1.0];
    CGRect target = _on ? CGRectMake(18, 2, 14, 14) : CGRectMake(2, 2, 14, 14);
    void (^blk)(void) = ^{ _track.backgroundColor = bg; _knob.frame = target; };
    if (animated) [UIView animateWithDuration:0.15 animations:blk];
    else blk();
}
@end

// ==================================================================
// custom slider: thin track + small thumb
// ==================================================================
@implementation RVSlider {
    UIView* _track;
    UIView* _fill;
    UIView* _thumb;
    float _t;
}
- (instancetype)init {
    if ((self = [super initWithFrame:CGRectMake(0,0,200,20)])) {
        self.userInteractionEnabled = YES;
        _minValue = 0; _maxValue = 100; _value = 0; _t = 0;
        _track = [UIView new];
        _track.backgroundColor = [UIColor colorWithRed:0.22 green:0.22 blue:0.24 alpha:1.0];
        _track.layer.cornerRadius = 1.5;
        [self addSubview:_track];
        _fill = [UIView new];
        _fill.backgroundColor = C_RED;
        _fill.layer.cornerRadius = 1.5;
        [self addSubview:_fill];
        _thumb = [UIView new];
        _thumb.backgroundColor = [UIColor whiteColor];
        _thumb.layer.cornerRadius = 5;
        [self addSubview:_thumb];
        [self addGestureRecognizer:[[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(onDrag:)]];
        [self addGestureRecognizer:[[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(onTap:)]];
    }
    return self;
}
- (void)layoutSubviews {
    [super layoutSubviews];
    CGFloat w = self.bounds.size.width;
    CGFloat h = self.bounds.size.height;
    CGFloat th = 3;
    CGFloat ty = (h - th)/2;
    _track.frame = CGRectMake(5, ty, w - 10, th);
    _fill.frame  = CGRectMake(5, ty, (w - 10) * _t, th);
    _thumb.frame = CGRectMake(5 + (w - 10) * _t - 5, h/2 - 5, 10, 10);
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
    CGFloat frac = MAX(0, MIN(1, (p.x - 5) / (w - 10)));
    float v = _minValue + frac * (_maxValue - _minValue);
    self.value = v;
    if (self.onChange) self.onChange(v);
}
- (void)onTap:(UITapGestureRecognizer*)g {
    CGPoint p = [g locationInView:self];
    CGFloat w = self.bounds.size.width;
    CGFloat frac = MAX(0, MIN(1, (p.x - 5) / (w - 10)));
    float v = _minValue + frac * (_maxValue - _minValue);
    self.value = v;
    if (self.onChange) self.onChange(v);
}
@end

// ==================================================================
// RavenMenu
// ==================================================================
@interface RavenMenu ()
@property (nonatomic, strong) UIWindow* window;
@property (nonatomic, strong) UIView*   panel;
@property (nonatomic, strong) UIView*   headerView;
@property (nonatomic, strong) UIView*   sidebarView;
@property (nonatomic, strong) UIView*   contentView;
@property (nonatomic, strong) UIView*   footerView;
@property (nonatomic, strong) UIView*   ball;
@property (nonatomic, strong) NSMutableArray* tabButtons;
@property (nonatomic, strong) NSMutableDictionary* tabViews;
@property (nonatomic, assign) NSInteger activeTab;
@property (nonatomic, strong) NSTimer* tickTimer;
@property (nonatomic, assign) BOOL panelOpen;
@property (nonatomic, assign) BOOL engineOn;
@end

@implementation RavenMenu

+ (instancetype)shared {
    static RavenMenu* s; static dispatch_once_t once;
    dispatch_once(&once, ^{ s = [RavenMenu new]; });
    return s;
}

- (void)start {
    if (self.window) return;
    [[RavenESP shared] attach];

    self.tabButtons = [NSMutableArray array];
    self.tabViews   = [NSMutableDictionary dictionary];
    self.activeTab  = 0;

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

// ==================================================================
// BALL — 46px circle, raven logo inside, no text
// ==================================================================
- (void)buildBall {
    CGFloat size = 46;
    CGRect scr = [UIScreen mainScreen].bounds;
    CGFloat x = scr.size.width - size - 16;
    CGFloat y = 110;
    self.ball = [[UIView alloc] initWithFrame:CGRectMake(x, y, size, size)];
    self.ball.backgroundColor = C_WIN;
    self.ball.layer.cornerRadius = size / 2.0;
    self.ball.layer.borderWidth = 1.5;
    self.ball.layer.borderColor = C_RED.CGColor;
    self.ball.layer.shadowColor = C_RED.CGColor;
    self.ball.layer.shadowOpacity = 0.6;
    self.ball.layer.shadowRadius = 10;
    self.ball.layer.shadowOffset = CGSizeZero;
    self.ball.userInteractionEnabled = YES;

    UIImage* mark = loadLogoURL(kBallLogoURL);
    if (mark) {
        UIImageView* iv = [[UIImageView alloc] initWithFrame:CGRectInset(self.ball.bounds, 3, 3)];
        iv.image = mark;
        iv.contentMode = UIViewContentModeScaleAspectFill;
        iv.layer.cornerRadius = (size - 6) / 2.0;
        iv.clipsToBounds = YES;
        iv.userInteractionEnabled = NO;
        [self.ball addSubview:iv];
    } else {
        UILabel* l = [[UILabel alloc] initWithFrame:self.ball.bounds];
        l.text = @"R"; l.textAlignment = NSTextAlignmentCenter;
        l.font = [UIFont systemFontOfSize:20 weight:UIFontWeightBold];
        l.textColor = C_RED;
        [self.ball addSubview:l];
    }
    [self.ball addGestureRecognizer:[[UITapGestureRecognizer alloc] initWithTarget:self action:@selector(togglePanel)]];
    [self.ball addGestureRecognizer:[[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(dragBall:)]];
}

- (void)togglePanel { self.panelOpen = !self.panelOpen; self.panel.hidden = !self.panelOpen; }
- (void)dragBall:(UIPanGestureRecognizer*)g {
    CGPoint t = [g translationInView:self.window];
    self.ball.center = CGPointMake(self.ball.center.x + t.x, self.ball.center.y + t.y);
    [g setTranslation:CGPointZero inView:self.window];
}

// ==================================================================
// PANEL — reference coords scaled to fit
// ==================================================================
- (void)buildPanel {
    CGRect scr = [UIScreen mainScreen].bounds;
    CGFloat availW = scr.size.width - 24;
    CGFloat availH = scr.size.height - 24;
    CGFloat scale = MIN(availW / kRefW, availH / kRefH);
    scale = MIN(1.0, scale);

    CGFloat W = kRefW * scale;
    CGFloat H = kRefH * scale;

    self.panel = [[UIView alloc] initWithFrame:CGRectMake((scr.size.width - W)/2,
                                                          (scr.size.height - H)/2,
                                                          W, H)];
    self.panel.backgroundColor = [UIColor clearColor];
    self.panel.layer.cornerRadius = 12 * scale;
    self.panel.layer.shadowColor = [UIColor blackColor].CGColor;
    self.panel.layer.shadowOpacity = 0.7;
    self.panel.layer.shadowRadius = 24 * scale;
    self.panel.layer.shadowOffset = CGSizeMake(0, 8 * scale);
    self.panel.clipsToBounds = NO;

    UIView* inner = [[UIView alloc] initWithFrame:CGRectMake(0, 0, kRefW, kRefH)];
    inner.backgroundColor = C_WIN;
    inner.layer.cornerRadius = 12;
    inner.layer.borderWidth = 1;
    inner.layer.borderColor = C_CRIMSON.CGColor;
    inner.clipsToBounds = YES;
    inner.transform = CGAffineTransformMakeScale(scale, scale);
    [self.panel addSubview:inner];

    [self buildHeader:CGRectMake(0, 0, kRefW, kHeaderH) into:inner];
    [self buildSidebar:CGRectMake(0, kHeaderH, kSidebarW, kRefH - kHeaderH - kFooterH) into:inner];
    [self buildContent:CGRectMake(kSidebarW, kHeaderH, kRefW - kSidebarW, kRefH - kHeaderH - kFooterH) into:inner];
    [self buildFooter:CGRectMake(0, kRefH - kFooterH, kRefW, kFooterH) into:inner];

    [self selectTab:0];
}

// ---------------- HEADER 50px ----------------
- (void)buildHeader:(CGRect)r into:(UIView*)parent {
    self.headerView = [[UIView alloc] initWithFrame:r];
    self.headerView.backgroundColor = C_HEAD;

    UIView* line = [[UIView alloc] initWithFrame:CGRectMake(0, r.size.height - 1, r.size.width, 1)];
    line.backgroundColor = [C_RED colorWithAlphaComponent:0.35];
    [self.headerView addSubview:line];

    // small 28x28 mark
    CGFloat ms = 28;
    UIView* markView = [[UIView alloc] initWithFrame:CGRectMake(14, (r.size.height - ms)/2, ms, ms)];
    markView.layer.cornerRadius = ms/2;
    markView.layer.borderWidth = 1;
    markView.layer.borderColor = C_RED.CGColor;
    markView.clipsToBounds = YES;
    UIImage* mark = loadLogoURL(kBallLogoURL);
    if (mark) {
        UIImageView* iv = [[UIImageView alloc] initWithFrame:markView.bounds];
        iv.image = mark; iv.contentMode = UIViewContentModeScaleAspectFill;
        [markView addSubview:iv];
    } else {
        markView.backgroundColor = C_RED;
    }
    [self.headerView addSubview:markView];

    // RAVEN wordmark image (small, header branding only)
    UIImage* wordmark = loadLogoURL(kWordmarkURL);
    if (wordmark) {
        CGFloat wh = 18; // fixed height, width scales
        CGFloat ww = wh * (wordmark.size.width / wordmark.size.height);
        UIImageView* wm = [[UIImageView alloc] initWithFrame:CGRectMake(14 + ms + 10, (r.size.height - wh)/2, ww, wh)];
        wm.image = wordmark;
        wm.contentMode = UIViewContentModeScaleAspectFit;
        wm.clipsToBounds = YES;
        [self.headerView addSubview:wm];
    } else {
        UILabel* title = lbl(@"RAVEN", 18, C_TEXT, YES);
        title.frame = CGRectMake(14 + ms + 10, 0, 200, r.size.height);
        [self.headerView addSubview:title];
    }

    // min 30x30
    UIButton* min = [UIButton buttonWithType:UIButtonTypeSystem];
    min.frame = CGRectMake(r.size.width - 82, (r.size.height - 30)/2, 30, 30);
    [min setTitle:@"—" forState:UIControlStateNormal];
    [min setTitleColor:C_SEC forState:UIControlStateNormal];
    min.titleLabel.font = [UIFont systemFontOfSize:18 weight:UIFontWeightSemibold];
    [min addTarget:self action:@selector(togglePanel) forControlEvents:UIControlEventTouchUpInside];
    [self.headerView addSubview:min];

    // close 30x30
    UIButton* close = [UIButton buttonWithType:UIButtonTypeSystem];
    close.frame = CGRectMake(r.size.width - 44, (r.size.height - 30)/2, 30, 30);
    [close setTitle:@"X" forState:UIControlStateNormal];
    [close setTitleColor:C_RED forState:UIControlStateNormal];
    close.titleLabel.font = [UIFont systemFontOfSize:15 weight:UIFontWeightBold];
    [close addTarget:self action:@selector(togglePanel) forControlEvents:UIControlEventTouchUpInside];
    [self.headerView addSubview:close];

    [parent addSubview:self.headerView];
}

// ---------------- SIDEBAR 165px ----------------
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

- (void)buildSidebar:(CGRect)r into:(UIView*)parent {
    self.sidebarView = [[UIView alloc] initWithFrame:r];
    self.sidebarView.backgroundColor = C_SIDE;
    self.sidebarView.clipsToBounds = YES;

    UIView* sep = [[UIView alloc] initWithFrame:CGRectMake(r.size.width - 1, 0, 1, r.size.height)];
    sep.backgroundColor = C_BORDER;
    [self.sidebarView addSubview:sep];

    // small emblem at top
    CGFloat em = 36;
    UIView* embView = [[UIView alloc] initWithFrame:CGRectMake((r.size.width - em)/2, 14, em, em)];
    embView.layer.cornerRadius = em/2;
    embView.layer.borderWidth = 1;
    embView.layer.borderColor = [C_RED colorWithAlphaComponent:0.5].CGColor;
    embView.clipsToBounds = YES;
    UIImage* art = loadLogoURL(kEmblemURL);
    if (art) {
        UIImageView* iv = [[UIImageView alloc] initWithFrame:embView.bounds];
        iv.image = art; iv.contentMode = UIViewContentModeScaleAspectFill;
        [embView addSubview:iv];
    } else {
        embView.backgroundColor = C_CRIMSON;
    }
    [self.sidebarView addSubview:embView];

    // tab list
    NSArray* defs = [self tabDefs];
    CGFloat y = 64;
    for (NSInteger i = 0; i < defs.count; i++) {
        NSDictionary* d = defs[i];
        std::string k = std::string([d[@"key"] UTF8String]);
        if (!Updater::feature(k, true)) continue;

        UIButton* btn = [UIButton buttonWithType:UIButtonTypeCustom];
        btn.frame = CGRectMake(0, y, r.size.width - 1, kTabH);
        btn.tag = i;
        btn.backgroundColor = [UIColor clearColor];
        [btn addTarget:self action:@selector(onTabTap:) forControlEvents:UIControlEventTouchUpInside];

        UIView* accent = [[UIView alloc] initWithFrame:CGRectMake(0, 6, 2, kTabH - 12)];
        accent.backgroundColor = [UIColor clearColor];
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

    // motto at bottom
    UILabel* m1 = lbl(@"SEE MORE.", 10, C_RED, YES);
    m1.textAlignment = NSTextAlignmentCenter;
    m1.frame = CGRectMake(0, r.size.height - 34, r.size.width, 14);
    [self.sidebarView addSubview:m1];
    UILabel* m2 = lbl(@"BE BETTER.", 10, C_RED, YES);
    m2.textAlignment = NSTextAlignmentCenter;
    m2.frame = CGRectMake(0, r.size.height - 20, r.size.width, 14);
    [self.sidebarView addSubview:m2];

    [parent addSubview:self.sidebarView];
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
        b.backgroundColor = active ? C_CRIMSON : [UIColor clearColor];
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

// ---------------- CONTENT ----------------
- (void)buildContent:(CGRect)r into:(UIView*)parent {
    self.contentView = [[UIView alloc] initWithFrame:r];
    self.contentView.backgroundColor = [UIColor clearColor];
    self.contentView.clipsToBounds = YES;
    [parent addSubview:self.contentView];
}

- (UIView*)buildTabContent:(NSString*)tab {
    UIScrollView* sv = [[UIScrollView alloc] initWithFrame:self.contentView.bounds];
    sv.backgroundColor = [UIColor clearColor];
    sv.showsVerticalScrollIndicator = NO;
    sv.contentInsetAdjustmentBehavior = UIScrollViewContentInsetAdjustmentNever;

    CGFloat W = sv.bounds.size.width;

    // page title block
    UILabel* title = lbl(tab, 18, C_TEXT, YES);
    title.frame = CGRectMake(kPad, 14, W - kPad*2, 22);
    [sv addSubview:title];

    UILabel* sub = lbl([self subtitleForTab:tab], 11, C_SEC, NO);
    sub.frame = CGRectMake(kPad, 38, W - kPad*2, 15);
    [sv addSubview:sub];

    // two-column card grid
    CGFloat startY = 68;
    CGFloat availW = W - kPad*2;
    CGFloat colW = (availW - kCardGap) / 2.0;

    NSArray* cards = [self cardsForTab:tab width:colW];
    CGFloat leftY = startY;
    CGFloat rightY = startY;

    for (NSInteger i = 0; i < (NSInteger)cards.count; i++) {
        UIView* c = cards[i];
        CGFloat h = c.frame.size.height;
        if ((i % 2) == 0) {
            c.frame = CGRectMake(kPad, leftY, colW, h);
            leftY += h + kCardGap;
        } else {
            c.frame = CGRectMake(kPad + colW + kCardGap, rightY, colW, h);
            rightY += h + kCardGap;
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

// ---------------- CARD ----------------
- (UIView*)card:(NSString*)title width:(CGFloat)w rows:(NSArray*)rows {
    UIView* card = [UIView new];
    card.backgroundColor = C_CARD;
    card.layer.cornerRadius = kCardRad;
    card.layer.borderWidth = 1;
    card.layer.borderColor = C_BORDER.CGColor;

    UILabel* t = lbl(title, 11, C_RED, YES);
    t.frame = CGRectMake(12, 10, w - 24, 14);
    [card addSubview:t];

    UIView* line = [[UIView alloc] initWithFrame:CGRectMake(12, 26, w - 24, 1)];
    line.backgroundColor = [C_RED colorWithAlphaComponent:0.15];
    [card addSubview:line];

    CGFloat y = 32;
    for (UIView* r in rows) {
        CGFloat rh = r.frame.size.height;
        r.frame = CGRectMake(0, y, w, rh);
        [card addSubview:r];
        y += rh;
    }
    y += 6;
    card.frame = CGRectMake(0, 0, w, y);
    return card;
}

// ---------------- ROW FACTORIES (return views sized within card) ----------------
- (UIView*)rowToggle:(NSString*)title on:(BOOL)on cb:(void(^)(BOOL))cb {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, kRowH)];
    UILabel* l = lbl(title, 13, C_TEXT, NO);
    l.frame = CGRectMake(12, 0, 160, kRowH);
    [row addSubview:l];
    RVToggle* t = [[RVToggle alloc] init];
    t.on = on;
    t.onChange = cb;
    t.frame = CGRectMake(row.frame.size.width - 46, (kRowH - 18)/2, 34, 18);
    t.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    [row addSubview:t];
    return row;
}

- (UIView*)rowSlider:(NSString*)title min:(float)mn max:(float)mx val:(float)v cb:(void(^)(float))cb {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, kRowHBig)];
    UILabel* l = lbl(title, 13, C_TEXT, NO);
    l.frame = CGRectMake(12, 4, 160, 16);
    [row addSubview:l];
    UILabel* val = lbl([NSString stringWithFormat:@"%.0f", v], 11, C_RED, YES);
    val.textAlignment = NSTextAlignmentRight;
    val.frame = CGRectMake(row.frame.size.width - 62, 4, 50, 16);
    val.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    [row addSubview:val];
    RVSlider* s = [[RVSlider alloc] init];
    s.minValue = mn; s.maxValue = mx; s.value = v;
    s.frame = CGRectMake(12, 22, row.frame.size.width - 24, 16);
    s.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    s.onChange = ^(float nv) { val.text = [NSString stringWithFormat:@"%.0f", nv]; if (cb) cb(nv); };
    [row addSubview:s];
    return row;
}

- (UIView*)rowDropdown:(NSString*)title value:(NSString*)val {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, kRowH)];
    UILabel* l = lbl(title, 13, C_TEXT, NO);
    l.frame = CGRectMake(12, 0, 140, kRowH);
    [row addSubview:l];

    UIView* pill = [[UIView alloc] initWithFrame:CGRectMake(row.frame.size.width - 92, 3, 80, 20)];
    pill.backgroundColor = [UIColor colorWithRed:0.102 green:0.102 blue:0.110 alpha:1.0];
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
    l.frame = CGRectMake(12, 0, 140, kRowH);
    [row addSubview:l];
    UILabel* v = lbl(val, 12, C_RED, YES);
    v.textAlignment = NSTextAlignmentRight;
    v.frame = CGRectMake(row.frame.size.width - 152, 0, 140, kRowH);
    v.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    [row addSubview:v];
    return row;
}

- (UIView*)rowButton:(NSString*)title tap:(void(^)(void))cb {
    UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, 34)];
    UIButton* b = [UIButton buttonWithType:UIButtonTypeCustom];
    b.frame = CGRectMake(10, 2, row.frame.size.width - 20, 30);
    b.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    [b setTitle:title forState:UIControlStateNormal];
    [b setTitleColor:C_TEXT forState:UIControlStateNormal];
    b.titleLabel.font = [UIFont systemFontOfSize:12 weight:UIFontWeightMedium];
    b.backgroundColor = [UIColor colorWithWhite:0.11 alpha:1.0];
    b.layer.cornerRadius = 5;
    b.layer.borderWidth = 1;
    b.layer.borderColor = C_BORDER.CGColor;
    // capture via block-bridge
    b.tag = (NSInteger)CFBridgingRetain([cb copy]);
    [b addTarget:self action:@selector(onGenericButton:) forControlEvents:UIControlEventTouchUpInside];
    [row addSubview:b];
    return row;
}

- (void)onGenericButton:(UIButton*)b {
    void (^cb)(void) = (__bridge void (^)(void))(void*)b.tag;
    if (cb) cb();
}

// ==================================================================
// CARDS PER TAB
// ==================================================================
- (NSArray*)cardsForTab:(NSString*)tab width:(CGFloat)w {
    if ([tab isEqualToString:@"AIMBOT"]) {
        UIView* general = [self card:@"GENERAL" width:w rows:@[
            [self rowToggle:@"Enable Aimbot" on:NO cb:^(BOOL v){ RavenAimbot::setEnabled(v); }],
            [self rowDropdown:@"Aim Activation" value:@"Hold"],
            [self rowSlider:@"Aim FOV" min:0 max:360 val:120 cb:^(float v){ RavenAimbot::setFov(v); }],
            [self rowSlider:@"Smoothness" min:1 max:30 val:5 cb:^(float v){ RavenAimbot::setSmooth(v); }],
        ]];
        UIView* advanced = [self card:@"ADVANCED" width:w rows:@[
            [self rowToggle:@"Prediction" on:YES cb:^(BOOL v){ RavenAimbot::setPrediction(v); }],
            [self rowSlider:@"Aim Delay" min:0 max:300 val:0 cb:nil],
            [self rowSlider:@"Target Switch Delay" min:0 max:500 val:120 cb:nil],
        ]];
        UIView* targeting = [self card:@"TARGETING" width:w rows:@[
            [self rowDropdown:@"Target Bone" value:@"Head"],
            [self rowDropdown:@"Target Priority" value:@"Distance"],
            [self rowToggle:@"Visible Check" on:YES cb:^(BOOL v){ RavenAimbot::setVisCheck(v); }],
            [self rowSlider:@"Max Distance" min:50 max:500 val:250 cb:nil],
        ]];
        UIView* fovCard = [self card:@"FOV" width:w rows:@[
            [self rowToggle:@"Show FOV Circle" on:YES cb:nil],
            [self rowSlider:@"FOV Radius" min:20 max:400 val:120 cb:nil],
            [self rowSlider:@"Circle Thickness" min:1 max:6 val:2 cb:nil],
        ]];
        return @[general, targeting, advanced, fovCard];
    }

    if ([tab isEqualToString:@"ESP"]) {
        UIView* player = [self card:@"PLAYER ESP" width:w rows:@[
            [self rowToggle:@"Enable ESP" on:YES cb:nil],
            [self rowToggle:@"Box" on:YES cb:nil],
            [self rowToggle:@"Corner Box" on:NO cb:nil],
            [self rowToggle:@"Skeleton" on:NO cb:nil],
            [self rowToggle:@"Snaplines" on:NO cb:nil],
        ]];
        UIView* info = [self card:@"INFORMATION" width:w rows:@[
            [self rowToggle:@"Name" on:YES cb:nil],
            [self rowToggle:@"Distance" on:YES cb:nil],
            [self rowToggle:@"Health" on:YES cb:nil],
            [self rowToggle:@"Weapon" on:NO cb:nil],
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
            [self rowToggle:@"Enable Crosshair" on:YES cb:nil],
            [self rowDropdown:@"Style" value:@"Dot"],
            [self rowSlider:@"Size" min:1 max:30 val:6 cb:nil],
            [self rowSlider:@"Thickness" min:1 max:6 val:2 cb:nil],
        ]];
        UIView* fov = [self card:@"FOV CIRCLE" width:w rows:@[
            [self rowToggle:@"Enable" on:NO cb:nil],
            [self rowSlider:@"Radius" min:20 max:400 val:120 cb:nil],
            [self rowSlider:@"Thickness" min:1 max:6 val:2 cb:nil],
        ]];
        UIView* world = [self card:@"WORLD VISUALS" width:w rows:@[
            [self rowToggle:@"Remove Fog" on:YES cb:nil],
            [self rowToggle:@"Night Mode" on:YES cb:nil],
            [self rowToggle:@"Brightness Boost" on:YES cb:nil],
            [self rowSlider:@"Brightness" min:0 max:200 val:100 cb:nil],
        ]];
        UIView* display = [self card:@"DISPLAY" width:w rows:@[
            [self rowToggle:@"No Flash" on:YES cb:nil],
            [self rowToggle:@"No Smoke" on:YES cb:nil],
            [self rowToggle:@"Better Textures" on:NO cb:nil],
        ]];
        return @[cross, fov, world, display];
    }

    if ([tab isEqualToString:@"WEAPON"]) {
        UIView* recoil = [self card:@"RECOIL" width:w rows:@[
            [self rowToggle:@"No Recoil" on:YES cb:nil],
            [self rowToggle:@"No Spread" on:YES cb:nil],
            [self rowSlider:@"Recoil Strength" min:0 max:100 val:0 cb:nil],
        ]];
        UIView* handling = [self card:@"HANDLING" width:w rows:@[
            [self rowToggle:@"Fast Reload" on:YES cb:nil],
            [self rowToggle:@"Rapid Fire" on:YES cb:nil],
            [self rowSlider:@"Fire Rate Multiplier" min:1 max:10 val:3 cb:nil],
        ]];
        UIView* effects = [self card:@"EFFECTS" width:w rows:@[
            [self rowToggle:@"No Flash" on:YES cb:nil],
            [self rowToggle:@"No Smoke" on:YES cb:nil],
            [self rowToggle:@"No Shell Casings" on:NO cb:nil],
        ]];
        return @[recoil, handling, effects];
    }

    if ([tab isEqualToString:@"MISC"]) {
        UIView* movement = [self card:@"MOVEMENT" width:w rows:@[
            [self rowToggle:@"Bunny Hop" on:YES cb:nil],
            [self rowToggle:@"Auto Strafe" on:YES cb:nil],
            [self rowToggle:@"No Fall Damage" on:NO cb:nil],
        ]];
        UIView* utility = [self card:@"UTILITY" width:w rows:@[
            [self rowToggle:@"Unlock All" on:NO cb:nil],
            [self rowToggle:@"No Ads" on:NO cb:nil],
            [self rowToggle:@"Panic Key" on:YES cb:nil],
        ]];
        UIView* iface = [self card:@"INTERFACE" width:w rows:@[
            [self rowToggle:@"Hide Menu When Closed" on:YES cb:nil],
            [self rowSlider:@"Menu Opacity" min:20 max:100 val:97 cb:nil],
        ]];
        return @[movement, utility, iface];
    }

    if ([tab isEqualToString:@"PLAYERS"]) {
        NSMutableArray* rowList = [NSMutableArray array];
        NSArray* names = @[@"Player_01", @"Player_02", @"Player_03", @"Player_04",
                           @"Kremityss", @"Devoo", @"VAMP", @"797 BUDDA"];
        NSArray* dists = @[@"24m", @"41m", @"58m", @"77m", @"12m", @"28m", @"104m", @"132m"];
        NSArray* statuses = @[@"Visible", @"Hidden", @"Visible", @"Visible",
                              @"Visible", @"Hidden", @"Visible", @"Hidden"];
        for (NSInteger i = 0; i < names.count; i++) {
            UIView* row = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 0, 24)];
            UILabel* n = lbl(names[i], 12, C_TEXT, NO);
            n.frame = CGRectMake(12, 0, 140, 24);
            [row addSubview:n];
            UILabel* d = lbl(dists[i], 11, C_SEC, NO);
            d.textAlignment = NSTextAlignmentCenter;
            d.frame = CGRectMake(row.frame.size.width - 130, 0, 60, 24);
            d.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
            [row addSubview:d];
            BOOL vis = [statuses[i] isEqualToString:@"Visible"];
            UILabel* s = lbl(statuses[i], 11, vis ? C_RED : C_MUTE, YES);
            s.textAlignment = NSTextAlignmentRight;
            s.frame = CGRectMake(row.frame.size.width - 66, 0, 56, 24);
            s.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
            [row addSubview:s];
            [rowList addObject:row];
        }
        UIView* list = [self card:@"PLAYER LIST" width:w rows:rowList];
        return @[list];
    }

    if ([tab isEqualToString:@"SETTINGS"]) {
        std::string rv = Updater::remoteVersion();
        NSString* rvStr = [NSString stringWithUTF8String:rv.c_str()];

        UIView* iface = [self card:@"INTERFACE" width:w rows:@[
            [self rowSlider:@"Menu Scale" min:50 max:150 val:100 cb:nil],
            [self rowDropdown:@"Accent Color" value:@"Crimson"],
            [self rowToggle:@"Animations" on:YES cb:nil],
        ]];
        UIView* config = [self card:@"CONFIG" width:w rows:@[
            [self rowButton:@"Save Config" tap:^{ RAVEN_LOG("save config"); }],
            [self rowButton:@"Load Config" tap:^{ RAVEN_LOG("load config"); }],
            [self rowButton:@"Reset to Defaults" tap:^{ RAVEN_LOG("reset"); }],
        ]];
        UIView* menu = [self card:@"MENU" width:w rows:@[
            [self rowDropdown:@"Open/Close Button" value:@"Floating"],
            [self rowDropdown:@"Position" value:@"Right"],
            [self rowSlider:@"Opacity" min:20 max:100 val:97 cb:nil],
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

// ---------------- FOOTER 28px ----------------
- (void)buildFooter:(CGRect)r into:(UIView*)parent {
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

    [parent addSubview:self.footerView];
}

// ==================================================================
- (void)onTick {
    if (!self.engineOn) return;
    [[RavenESP shared] begin];
    [[RavenESP shared] render];
    RavenAimbot::tick();
}

@end
""")
