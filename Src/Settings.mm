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
int   aimPriority = 0;
int   aimCurve = 1;

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
int   espBoxStyle = 0;

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

int   uiAccentColor = 0;
int   uiOpenButton = 0;
int   uiPosition = 0;

static NSString* kKey(NSString* n) { return [@"raven." stringByAppendingString:n]; }

void load() {
    NSUserDefaults* d = [NSUserDefaults standardUserDefaults];
    aimEnabled = [d boolForKey:kKey(@"aim.enabled")];
    aimFov = [d floatForKey:kKey(@"aim.fov")];  if (aimFov <= 0) aimFov = 120;
    aimSmooth = [d floatForKey:kKey(@"aim.smooth")]; if (aimSmooth <= 0) aimSmooth = 5;
    espEnabled = [d objectForKey:kKey(@"esp.enabled")] ? [d boolForKey:kKey(@"esp.enabled")] : YES;
    miscMenuOpacity = [d floatForKey:kKey(@"misc.opacity")]; if (miscMenuOpacity <= 0) miscMenuOpacity = 97;
    menuScale = [d floatForKey:kKey(@"ui.scale")]; if (menuScale <= 0) menuScale = 100;

    aimActivation   = (int)[d integerForKey:kKey(@"aim.activation")];
    aimBone         = (int)[d integerForKey:kKey(@"aim.bone")];
    espEnemyColor   = (int)[d integerForKey:kKey(@"esp.enemyColor")];
    espVisibleColor = (int)[d integerForKey:kKey(@"esp.visibleColor")];
    espSkeletonColor= (int)[d integerForKey:kKey(@"esp.skeletonColor")];
    espBoxColor     = (int)[d integerForKey:kKey(@"esp.boxColor")];
    espBoxStyle     = (int)[d integerForKey:kKey(@"esp.boxStyle")];
    visCrosshairStyle = (int)[d integerForKey:kKey(@"vis.crosshairStyle")];
    aimPriority     = (int)[d integerForKey:kKey(@"aim.priority")];
    aimCurve        = [d objectForKey:kKey(@"aim.curve")] ? (int)[d integerForKey:kKey(@"aim.curve")] : aimCurve;
    uiAccentColor   = (int)[d integerForKey:kKey(@"ui.accent")];
    uiOpenButton    = (int)[d integerForKey:kKey(@"ui.openButton")];
    uiPosition      = (int)[d integerForKey:kKey(@"ui.position")];
    animations      = [d objectForKey:kKey(@"ui.animations")] ? [d boolForKey:kKey(@"ui.animations")] : YES;

    aimMaxDist = [d objectForKey:kKey(@"aim.maxDist")] ? [d floatForKey:kKey(@"aim.maxDist")] : aimMaxDist;
    aimPrediction = [d objectForKey:kKey(@"aim.prediction")] ? [d boolForKey:kKey(@"aim.prediction")] : aimPrediction;
    aimVisCheck = [d objectForKey:kKey(@"aim.visCheck")] ? [d boolForKey:kKey(@"aim.visCheck")] : aimVisCheck;
    aimDelay = [d objectForKey:kKey(@"aim.delay")] ? [d floatForKey:kKey(@"aim.delay")] : aimDelay;
    aimSwitchDelay = [d objectForKey:kKey(@"aim.switchDelay")] ? [d floatForKey:kKey(@"aim.switchDelay")] : aimSwitchDelay;
    aimShowCircle = [d objectForKey:kKey(@"aim.showCircle")] ? [d boolForKey:kKey(@"aim.showCircle")] : aimShowCircle;
    aimCircleRadius = [d objectForKey:kKey(@"aim.circleRadius")] ? [d floatForKey:kKey(@"aim.circleRadius")] : aimCircleRadius;
    aimCircleThickness = [d objectForKey:kKey(@"aim.circleThickness")] ? [d floatForKey:kKey(@"aim.circleThickness")] : aimCircleThickness;
    espBox = [d objectForKey:kKey(@"esp.box")] ? [d boolForKey:kKey(@"esp.box")] : espBox;
    espCorner = [d objectForKey:kKey(@"esp.corner")] ? [d boolForKey:kKey(@"esp.corner")] : espCorner;
    espSkeleton = [d objectForKey:kKey(@"esp.skeleton")] ? [d boolForKey:kKey(@"esp.skeleton")] : espSkeleton;
    espSnaplines = [d objectForKey:kKey(@"esp.snaplines")] ? [d boolForKey:kKey(@"esp.snaplines")] : espSnaplines;
    espName = [d objectForKey:kKey(@"esp.name")] ? [d boolForKey:kKey(@"esp.name")] : espName;
    espDistance = [d objectForKey:kKey(@"esp.distance")] ? [d boolForKey:kKey(@"esp.distance")] : espDistance;
    espHealth = [d objectForKey:kKey(@"esp.health")] ? [d boolForKey:kKey(@"esp.health")] : espHealth;
    espWeapon = [d objectForKey:kKey(@"esp.weapon")] ? [d boolForKey:kKey(@"esp.weapon")] : espWeapon;
    visCrosshair = [d objectForKey:kKey(@"vis.crosshair")] ? [d boolForKey:kKey(@"vis.crosshair")] : visCrosshair;
    visCrosshairSize = [d objectForKey:kKey(@"vis.crosshairSize")] ? [d floatForKey:kKey(@"vis.crosshairSize")] : visCrosshairSize;
    visCrosshairThickness = [d objectForKey:kKey(@"vis.crosshairThickness")] ? [d floatForKey:kKey(@"vis.crosshairThickness")] : visCrosshairThickness;
    visFovCircle = [d objectForKey:kKey(@"vis.fovCircle")] ? [d boolForKey:kKey(@"vis.fovCircle")] : visFovCircle;
    visFovRadius = [d objectForKey:kKey(@"vis.fovRadius")] ? [d floatForKey:kKey(@"vis.fovRadius")] : visFovRadius;
    visFovThickness = [d objectForKey:kKey(@"vis.fovThickness")] ? [d floatForKey:kKey(@"vis.fovThickness")] : visFovThickness;
    visRemoveFog = [d objectForKey:kKey(@"vis.removeFog")] ? [d boolForKey:kKey(@"vis.removeFog")] : visRemoveFog;
    visNightMode = [d objectForKey:kKey(@"vis.nightMode")] ? [d boolForKey:kKey(@"vis.nightMode")] : visNightMode;
    visBrightnessBoost = [d objectForKey:kKey(@"vis.brightnessBoost")] ? [d boolForKey:kKey(@"vis.brightnessBoost")] : visBrightnessBoost;
    visBrightness = [d objectForKey:kKey(@"vis.brightness")] ? [d floatForKey:kKey(@"vis.brightness")] : visBrightness;
    visNoFlash = [d objectForKey:kKey(@"vis.noFlash")] ? [d boolForKey:kKey(@"vis.noFlash")] : visNoFlash;
    visNoSmoke = [d objectForKey:kKey(@"vis.noSmoke")] ? [d boolForKey:kKey(@"vis.noSmoke")] : visNoSmoke;
    visBetterTextures = [d objectForKey:kKey(@"vis.betterTextures")] ? [d boolForKey:kKey(@"vis.betterTextures")] : visBetterTextures;
    wpnNoRecoil = [d objectForKey:kKey(@"wpn.noRecoil")] ? [d boolForKey:kKey(@"wpn.noRecoil")] : wpnNoRecoil;
    wpnNoSpread = [d objectForKey:kKey(@"wpn.noSpread")] ? [d boolForKey:kKey(@"wpn.noSpread")] : wpnNoSpread;
    wpnRecoilStrength = [d objectForKey:kKey(@"wpn.recoilStrength")] ? [d floatForKey:kKey(@"wpn.recoilStrength")] : wpnRecoilStrength;
    wpnFastReload = [d objectForKey:kKey(@"wpn.fastReload")] ? [d boolForKey:kKey(@"wpn.fastReload")] : wpnFastReload;
    wpnRapidFire = [d objectForKey:kKey(@"wpn.rapidFire")] ? [d boolForKey:kKey(@"wpn.rapidFire")] : wpnRapidFire;
    wpnFireRate = [d objectForKey:kKey(@"wpn.fireRate")] ? [d floatForKey:kKey(@"wpn.fireRate")] : wpnFireRate;
    wpnNoFlash = [d objectForKey:kKey(@"wpn.noFlash")] ? [d boolForKey:kKey(@"wpn.noFlash")] : wpnNoFlash;
    wpnNoSmoke = [d objectForKey:kKey(@"wpn.noSmoke")] ? [d boolForKey:kKey(@"wpn.noSmoke")] : wpnNoSmoke;
    wpnNoShells = [d objectForKey:kKey(@"wpn.noShells")] ? [d boolForKey:kKey(@"wpn.noShells")] : wpnNoShells;
    miscBunnyHop = [d objectForKey:kKey(@"misc.bunnyHop")] ? [d boolForKey:kKey(@"misc.bunnyHop")] : miscBunnyHop;
    miscAutoStrafe = [d objectForKey:kKey(@"misc.autoStrafe")] ? [d boolForKey:kKey(@"misc.autoStrafe")] : miscAutoStrafe;
    miscNoFallDamage = [d objectForKey:kKey(@"misc.noFallDamage")] ? [d boolForKey:kKey(@"misc.noFallDamage")] : miscNoFallDamage;
    miscUnlockAll = [d objectForKey:kKey(@"misc.unlockAll")] ? [d boolForKey:kKey(@"misc.unlockAll")] : miscUnlockAll;
    miscNoAds = [d objectForKey:kKey(@"misc.noAds")] ? [d boolForKey:kKey(@"misc.noAds")] : miscNoAds;
    miscPanicKey = [d objectForKey:kKey(@"misc.panicKey")] ? [d boolForKey:kKey(@"misc.panicKey")] : miscPanicKey;
    miscHideWhenClosed = [d objectForKey:kKey(@"misc.hideWhenClosed")] ? [d boolForKey:kKey(@"misc.hideWhenClosed")] : miscHideWhenClosed;
}

void save() {
    NSUserDefaults* d = [NSUserDefaults standardUserDefaults];
    [d setBool:aimEnabled forKey:kKey(@"aim.enabled")];
    [d setFloat:aimFov forKey:kKey(@"aim.fov")];
    [d setFloat:aimSmooth forKey:kKey(@"aim.smooth")];
    [d setBool:espEnabled forKey:kKey(@"esp.enabled")];
    [d setFloat:miscMenuOpacity forKey:kKey(@"misc.opacity")];
    [d setFloat:menuScale forKey:kKey(@"ui.scale")];

    [d setInteger:aimActivation forKey:kKey(@"aim.activation")];
    [d setInteger:aimBone forKey:kKey(@"aim.bone")];
    [d setInteger:espEnemyColor forKey:kKey(@"esp.enemyColor")];
    [d setInteger:espVisibleColor forKey:kKey(@"esp.visibleColor")];
    [d setInteger:espSkeletonColor forKey:kKey(@"esp.skeletonColor")];
    [d setInteger:espBoxColor forKey:kKey(@"esp.boxColor")];
    [d setInteger:espBoxStyle forKey:kKey(@"esp.boxStyle")];
    [d setInteger:visCrosshairStyle forKey:kKey(@"vis.crosshairStyle")];
    [d setInteger:aimPriority forKey:kKey(@"aim.priority")];
    [d setInteger:aimCurve forKey:kKey(@"aim.curve")];
    [d setInteger:uiAccentColor forKey:kKey(@"ui.accent")];
    [d setInteger:uiOpenButton forKey:kKey(@"ui.openButton")];
    [d setInteger:uiPosition forKey:kKey(@"ui.position")];
    [d setBool:animations forKey:kKey(@"ui.animations")];
    [d setFloat:aimMaxDist forKey:kKey(@"aim.maxDist")];
    [d setBool:aimPrediction forKey:kKey(@"aim.prediction")];
    [d setBool:aimVisCheck forKey:kKey(@"aim.visCheck")];
    [d setFloat:aimDelay forKey:kKey(@"aim.delay")];
    [d setFloat:aimSwitchDelay forKey:kKey(@"aim.switchDelay")];
    [d setBool:aimShowCircle forKey:kKey(@"aim.showCircle")];
    [d setFloat:aimCircleRadius forKey:kKey(@"aim.circleRadius")];
    [d setFloat:aimCircleThickness forKey:kKey(@"aim.circleThickness")];
    [d setBool:espBox forKey:kKey(@"esp.box")];
    [d setBool:espCorner forKey:kKey(@"esp.corner")];
    [d setBool:espSkeleton forKey:kKey(@"esp.skeleton")];
    [d setBool:espSnaplines forKey:kKey(@"esp.snaplines")];
    [d setBool:espName forKey:kKey(@"esp.name")];
    [d setBool:espDistance forKey:kKey(@"esp.distance")];
    [d setBool:espHealth forKey:kKey(@"esp.health")];
    [d setBool:espWeapon forKey:kKey(@"esp.weapon")];
    [d setBool:visCrosshair forKey:kKey(@"vis.crosshair")];
    [d setFloat:visCrosshairSize forKey:kKey(@"vis.crosshairSize")];
    [d setFloat:visCrosshairThickness forKey:kKey(@"vis.crosshairThickness")];
    [d setBool:visFovCircle forKey:kKey(@"vis.fovCircle")];
    [d setFloat:visFovRadius forKey:kKey(@"vis.fovRadius")];
    [d setFloat:visFovThickness forKey:kKey(@"vis.fovThickness")];
    [d setBool:visRemoveFog forKey:kKey(@"vis.removeFog")];
    [d setBool:visNightMode forKey:kKey(@"vis.nightMode")];
    [d setBool:visBrightnessBoost forKey:kKey(@"vis.brightnessBoost")];
    [d setFloat:visBrightness forKey:kKey(@"vis.brightness")];
    [d setBool:visNoFlash forKey:kKey(@"vis.noFlash")];
    [d setBool:visNoSmoke forKey:kKey(@"vis.noSmoke")];
    [d setBool:visBetterTextures forKey:kKey(@"vis.betterTextures")];
    [d setBool:wpnNoRecoil forKey:kKey(@"wpn.noRecoil")];
    [d setBool:wpnNoSpread forKey:kKey(@"wpn.noSpread")];
    [d setFloat:wpnRecoilStrength forKey:kKey(@"wpn.recoilStrength")];
    [d setBool:wpnFastReload forKey:kKey(@"wpn.fastReload")];
    [d setBool:wpnRapidFire forKey:kKey(@"wpn.rapidFire")];
    [d setFloat:wpnFireRate forKey:kKey(@"wpn.fireRate")];
    [d setBool:wpnNoFlash forKey:kKey(@"wpn.noFlash")];
    [d setBool:wpnNoSmoke forKey:kKey(@"wpn.noSmoke")];
    [d setBool:wpnNoShells forKey:kKey(@"wpn.noShells")];
    [d setBool:miscBunnyHop forKey:kKey(@"misc.bunnyHop")];
    [d setBool:miscAutoStrafe forKey:kKey(@"misc.autoStrafe")];
    [d setBool:miscNoFallDamage forKey:kKey(@"misc.noFallDamage")];
    [d setBool:miscUnlockAll forKey:kKey(@"misc.unlockAll")];
    [d setBool:miscNoAds forKey:kKey(@"misc.noAds")];
    [d setBool:miscPanicKey forKey:kKey(@"misc.panicKey")];
    [d setBool:miscHideWhenClosed forKey:kKey(@"misc.hideWhenClosed")];
    [d synchronize];
}

void resetToDefaults() {
    aimEnabled = false;
    aimBone = 0;
    aimActivation = 0;
    aimFov = 120.0f;
    aimSmooth = 5.0f;
    aimMaxDist = 250.0f;
    aimPrediction = true;
    aimVisCheck = true;
    aimDelay = 0.0f;
    aimSwitchDelay = 120.0f;
    aimShowCircle = true;
    aimCircleRadius = 120.0f;
    aimCircleThickness = 2.0f;
    aimPriority = 0;
    aimCurve = 1;

    espEnabled = true;
    espBox = true;
    espCorner = false;
    espSkeleton = false;
    espSnaplines = false;
    espName = true;
    espDistance = true;
    espHealth = true;
    espWeapon = false;
    espEnemyColor = 0;
    espVisibleColor = 1;
    espSkeletonColor = 2;
    espBoxColor = 0;
    espBoxStyle = 0;

    visCrosshair = true;
    visCrosshairStyle = 0;
    visCrosshairSize = 6.0f;
    visCrosshairThickness = 2.0f;
    visFovCircle = false;
    visFovRadius = 120.0f;
    visFovThickness = 2.0f;
    visRemoveFog = true;
    visNightMode = true;
    visBrightnessBoost = true;
    visBrightness = 100.0f;
    visNoFlash = true;
    visNoSmoke = true;
    visBetterTextures = false;

    wpnNoRecoil = true;
    wpnNoSpread = true;
    wpnRecoilStrength = 0.0f;
    wpnFastReload = true;
    wpnRapidFire = true;
    wpnFireRate = 3.0f;
    wpnNoFlash = true;
    wpnNoSmoke = true;
    wpnNoShells = false;

    miscBunnyHop = true;
    miscAutoStrafe = true;
    miscNoFallDamage = false;
    miscUnlockAll = false;
    miscNoAds = false;
    miscPanicKey = true;
    miscHideWhenClosed = true;
    miscMenuOpacity = 97.0f;

    menuScale = 100.0f;
    animations = true;
    uiAccentColor = 0;
    uiOpenButton = 0;
    uiPosition = 0;

    save();
}

}
