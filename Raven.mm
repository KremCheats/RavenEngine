#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <dispatch/dispatch.h>
#import "Src/Common.h"
#import "Src/IL2CPP.h"
#import "Src/Menu.h"
#import "Src/Updater.h"
#import "Src/Logos.h"
#import "Src/Settings.h"
#import "Src/LicenseClient.h"

static UIViewController* ravenTopController(void) {
    UIWindow* window = nil;
    for (UIScene* scene in [UIApplication sharedApplication].connectedScenes) {
        if (scene.activationState == UISceneActivationStateForegroundActive &&
            [scene isKindOfClass:[UIWindowScene class]]) {
            for (UIWindow* candidate in ((UIWindowScene*)scene).windows) {
                if (candidate.isKeyWindow) { window = candidate; break; }
            }
        }
        if (window) break;
    }
    if (!window) window = [UIApplication sharedApplication].keyWindow;
    UIViewController* controller = window.rootViewController;
    while (controller.presentedViewController) controller = controller.presentedViewController;
    if ([controller isKindOfClass:[UINavigationController class]]) controller = [(UINavigationController*)controller visibleViewController];
    if ([controller isKindOfClass:[UITabBarController class]]) controller = [(UITabBarController*)controller selectedViewController];
    return controller;
}

static void ravenShowKeyPrompt(NSString* message) {
    dispatch_async(dispatch_get_main_queue(), ^{
        UIViewController* presenter = ravenTopController();
        if (!presenter) {
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
                ravenShowKeyPrompt(message);
            });
            return;
        }
        UIAlertController* alert = [UIAlertController alertControllerWithTitle:@"Raven License"
                                                                         message:message ?: @"Enter your license key to continue."
                                                                  preferredStyle:UIAlertControllerStyleAlert];
        [alert addTextFieldWithConfigurationHandler:^(UITextField* field) {
            field.placeholder = @"KREM-COMBAT-MASTER-XXXX";
            field.autocapitalizationType = UITextAutocapitalizationTypeAllCharacters;
            field.clearButtonMode = UITextFieldViewModeWhileEditing;
        }];
        [alert addAction:[UIAlertAction actionWithTitle:@"Cancel" style:UIAlertActionStyleCancel handler:nil]];
        [alert addAction:[UIAlertAction actionWithTitle:@"Validate" style:UIAlertActionStyleDefault handler:^(UIAlertAction* action) {
            NSString* key = [alert.textFields.firstObject.text stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]].uppercaseString;
            if (!key.length) { ravenShowKeyPrompt(@"A license key is required."); return; }
            NSUserDefaults* defaults = [NSUserDefaults standardUserDefaults];
            NSString* hwid = RavenLicense::deviceFingerprint();
            [defaults setObject:key forKey:@"raven.license.key"];
            [defaults setObject:hwid forKey:@"raven.license.hwid"];
            [defaults synchronize];
            RavenLicense::validateAsync(key, hwid, ^(BOOL valid, NSString* reason) {
                if (valid) {
                    RAVEN_LOG("license: validated from prompt");
                    return;
                }
                [defaults removeObjectForKey:@"raven.license.key"];
                [defaults synchronize];
                ravenShowKeyPrompt([NSString stringWithFormat:@"License validation failed: %@", reason ?: @"unknown"]);
            });
        }]];
        [presenter presentViewController:alert animated:YES completion:nil];
    });
}

__attribute__((constructor))
static void raven_entry(void) {
    @autoreleasepool {
        RAVEN_LOG("entry");
        RavenSettings::load();
        RAVEN_LOG("settings: aimEnabled=%d espEnabled=%d aimActivation=%d",
                  RavenSettings::aimEnabled,
                  RavenSettings::espEnabled,
                  RavenSettings::aimActivation);
        RavenLicense::validateStoredAsync(^(BOOL valid, NSString* reason) {
            if (!valid) {
                RavenSettings::aimEnabled = false;
                RavenSettings::espEnabled = false;
                RAVEN_LOG("license: rejected reason=%@", reason ?: @"unknown");
                if ([reason isEqualToString:@"credentials_missing"])
                    ravenShowKeyPrompt(@"Enter your Raven license key to activate this device.");
            } else {
                RAVEN_LOG("license: validated");
            }
        });
        Updater::fetchAsync(kConfigURL);
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(4 * NSEC_PER_SEC)),
                       dispatch_get_main_queue(), ^{
            IL2CPP::init();
            [[RavenMenu shared] start];
        });
    }
}
