#import "LicenseClient.h"
#import "Common.h"
#import "Settings.h"
#import <UIKit/UIKit.h>
#import <CommonCrypto/CommonDigest.h>

#include <dispatch/dispatch.h>
#include <cstring>

namespace RavenLicense {

// Keep this endpoint in one place. Release builds should point it at the
// published portal domain; the sandbox preview URL is intentionally not
// hard-coded into the tweak artifact.
static NSString* const kValidationEndpoint = @"https://3000-ifms2n9u4w28defd9v650-2547e316.us4.manus.computer/api/trpc/license.validate?batch=1";

NSString* deviceFingerprint(void) {
    UIDevice* device = [UIDevice currentDevice];
    NSString* vendorUUID = device.identifierForVendor.UUIDString;
    if (vendorUUID.length) return vendorUUID.lowercaseString;

    // Rare fallback for environments without identifierForVendor. It remains
    // UUID-shaped so the portal contract stays identical.
    NSString* material = [NSString stringWithFormat:@"raven-v1|%@|%@", device.model ?: @"unknown", device.systemVersion ?: @"unknown"];
    unsigned char digest[CC_SHA256_DIGEST_LENGTH] = {0};
    CC_SHA256(material.UTF8String, (CC_LONG)strlen(material.UTF8String), digest);
    digest[6] = (digest[6] & 0x0f) | 0x50;
    digest[8] = (digest[8] & 0x3f) | 0x80;
    NSString* result = [NSString stringWithFormat:@"%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
                        digest[0], digest[1], digest[2], digest[3], digest[4], digest[5], digest[6], digest[7],
                        digest[8], digest[9], digest[10], digest[11], digest[12], digest[13], digest[14], digest[15]];
    return result;
}

void validateAsync(NSString* key, NSString* hwid, ValidationCallback callback) {
    if (!key.length || !hwid.length || !callback) return;
    NSURL* url = [NSURL URLWithString:kValidationEndpoint];
    if (!url) { callback(NO, @"invalid_endpoint"); return; }

    NSDictionary* input = @{ @"0": @{ @"json": @{ @"key": key, @"hwid": hwid } } };
    NSError* jsonError = nil;
    NSData* body = [NSJSONSerialization dataWithJSONObject:input options:0 error:&jsonError];
    if (!body) { callback(NO, @"request_encoding_failed"); return; }

    NSMutableURLRequest* request = [NSMutableURLRequest requestWithURL:url];
    request.HTTPMethod = @"POST";
    request.HTTPBody = body;
    [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
    [request setValue:@"Raven/1" forHTTPHeaderField:@"User-Agent"];

    [[[NSURLSession sharedSession] dataTaskWithRequest:request completionHandler:^(NSData* data, NSURLResponse* response, NSError* error) {
        if (error || !data) { dispatch_async(dispatch_get_main_queue(), ^{ callback(NO, @"network_error"); }); return; }
        NSError* parseError = nil;
        id outer = [NSJSONSerialization JSONObjectWithData:data options:0 error:&parseError];
        NSDictionary* envelope = nil;
        if ([outer isKindOfClass:[NSArray class]]) {
            id first = [(NSArray*)outer firstObject];
            if ([first isKindOfClass:[NSDictionary class]]) envelope = first;
        } else if ([outer isKindOfClass:[NSDictionary class]]) {
            id batch = [(NSDictionary*)outer objectForKeyedSubscript:@"0"];
            if ([batch isKindOfClass:[NSDictionary class]]) envelope = batch;
            else if ([batch isKindOfClass:[NSArray class]]) {
                id first = [(NSArray*)batch firstObject];
                if ([first isKindOfClass:[NSDictionary class]]) envelope = first;
            }
        }
        NSDictionary* result = [envelope[@"result"] isKindOfClass:[NSDictionary class]] ? envelope[@"result"] : nil;
        NSDictionary* dataObject = [result[@"data"] isKindOfClass:[NSDictionary class]] ? result[@"data"] : nil;
        NSDictionary* json = [dataObject[@"json"] isKindOfClass:[NSDictionary class]] ? dataObject[@"json"] : nil;
        BOOL valid = [json[@"valid"] boolValue];
        NSString* reason = [json[@"reason"] isKindOfClass:[NSString class]] ? json[@"reason"] : (parseError || !json ? @"invalid_response" : @"unknown");
        dispatch_async(dispatch_get_main_queue(), ^{ callback(valid, reason); });
    }] resume];
}

void validateStoredAsync(ValidationCallback callback) {
    NSUserDefaults* defaults = [NSUserDefaults standardUserDefaults];
    NSString* key = [defaults stringForKey:@"raven.license.key"];
    NSString* hwid = [defaults stringForKey:@"raven.license.hwid"];
    if (!key.length) { if (callback) callback(NO, @"credentials_missing"); return; }
    if (!hwid.length) {
        hwid = deviceFingerprint();
        [defaults setObject:hwid forKey:@"raven.license.hwid"];
        [defaults synchronize];
    }
    validateAsync(key, hwid, callback);
}

}
