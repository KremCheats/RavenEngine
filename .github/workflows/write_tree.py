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

TWEAK_NAME = Dumper
Dumper_FILES = Dumper.mm
Dumper_CFLAGS = -fobjc-arc -std=c++17
Dumper_CCFLAGS = -fobjc-arc -std=c++17
Dumper_FRAMEWORKS = UIKit Foundation

include $(THEOS_MAKE_PATH)/tweak.mk
""")

w("Dumper.mm", r"""
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <dispatch/dispatch.h>
#import <dlfcn.h>
#import <string.h>
#import <stdio.h>
#import <mach-o/dyld.h>

// ------- il2cpp API typedefs -------
typedef void*   (*t_domain_get)();
typedef void*   (*t_thread_attach)(void*);
typedef size_t  (*t_domain_get_assemblies)(void*, size_t*);
typedef void*   (*t_assembly_get_image)(void*);
typedef size_t  (*t_image_get_class_count)(void*);
typedef void*   (*t_image_get_class)(void*, size_t);
typedef const char* (*t_class_get_name)(void*);
typedef const char* (*t_class_get_namespace)(void*);
typedef void*   (*t_class_get_fields)(void*, void**);
typedef const char* (*t_field_get_name)(void*);
typedef uint32_t (*t_field_get_offset)(void*);
typedef void*   (*t_class_get_methods)(void*, void**);
typedef const char* (*t_method_get_name)(void*);
typedef uint32_t (*t_method_get_param_count)(void*);

static t_domain_get p_domain_get = nullptr;
static t_thread_attach p_thread_attach = nullptr;
static t_domain_get_assemblies p_domain_get_assemblies = nullptr;
static t_assembly_get_image p_assembly_get_image = nullptr;
static t_image_get_class_count p_image_get_class_count = nullptr;
static t_image_get_class p_image_get_class = nullptr;
static t_class_get_name p_class_get_name = nullptr;
static t_class_get_namespace p_class_get_namespace = nullptr;
static t_class_get_fields p_class_get_fields = nullptr;
static t_field_get_name p_field_get_name = nullptr;
static t_field_get_offset p_field_get_offset = nullptr;
static t_class_get_methods p_class_get_methods = nullptr;
static t_method_get_name p_method_get_name = nullptr;
static t_method_get_param_count p_method_get_param_count = nullptr;

static void* rs(const char* n) { return dlsym(RTLD_DEFAULT, n); }

static void dumpEverything() {
    NSLog(@"[dumper] starting dump");

    p_domain_get             = (t_domain_get)             rs("il2cpp_domain_get");
    p_thread_attach          = (t_thread_attach)          rs("il2cpp_thread_attach");
    p_domain_get_assemblies  = (t_domain_get_assemblies)  rs("il2cpp_domain_get_assemblies");
    p_assembly_get_image     = (t_assembly_get_image)     rs("il2cpp_assembly_get_image");
    p_image_get_class_count  = (t_image_get_class_count)  rs("il2cpp_image_get_class_count");
    p_image_get_class        = (t_image_get_class)        rs("il2cpp_image_get_class");
    p_class_get_name         = (t_class_get_name)         rs("il2cpp_class_get_name");
    p_class_get_namespace    = (t_class_get_namespace)    rs("il2cpp_class_get_namespace");
    p_class_get_fields       = (t_class_get_fields)       rs("il2cpp_class_get_fields");
    p_field_get_name         = (t_field_get_name)         rs("il2cpp_field_get_name");
    p_field_get_offset       = (t_field_get_offset)       rs("il2cpp_field_get_offset");
    p_class_get_methods      = (t_class_get_methods)      rs("il2cpp_class_get_methods");
    p_method_get_name        = (t_method_get_name)        rs("il2cpp_method_get_name");
    p_method_get_param_count = (t_method_get_param_count) rs("il2cpp_method_get_param_count");

    if (!p_domain_get || !p_domain_get_assemblies || !p_assembly_get_image) {
        NSLog(@"[dumper] il2cpp API missing");
        return;
    }

    void* domain = p_domain_get();
    if (!domain) { NSLog(@"[dumper] null domain"); return; }
    if (p_thread_attach) p_thread_attach(domain);

    size_t n = 0;
    void** assemblies = (void**)p_domain_get_assemblies(domain, &n);
    NSLog(@"[dumper] assemblies: %zu", n);

    FILE* f = fopen("/tmp/cm_dump.txt", "w");
    if (!f) { NSLog(@"[dumper] cannot open dump file"); return; }

    for (size_t a = 0; a < n; a++) {
        void* img = p_assembly_get_image(assemblies[a]);
        if (!img) continue;
        size_t cc = p_image_get_class_count(img);
        fprintf(f, "\n===== assembly %zu : %zu classes =====\n", a, cc);

        for (size_t i = 0; i < cc; i++) {
            void* klass = p_image_get_class(img, i);
            if (!klass) continue;
            const char* cname = p_class_get_name(klass);
            const char* cns = p_class_get_namespace(klass);
            fprintf(f, "\nCLASS %s::%s\n", cns ? cns : "", cname ? cname : "");

            // fields
            void* fiter = nullptr;
            while (1) {
                void* fld = p_class_get_fields(klass, &fiter);
                if (!fld) break;
                const char* fn = p_field_get_name(fld);
                uint32_t off = p_field_get_offset(fld);
                fprintf(f, "    F %s @ 0x%X\n", fn ? fn : "?", off);
            }

            // methods
            void* miter = nullptr;
            while (1) {
                void* m = p_class_get_methods(klass, &miter);
                if (!m) break;
                const char* mn = p_method_get_name(m);
                uint32_t pc = p_method_get_param_count(m);
                fprintf(f, "    M %s (%u)\n", mn ? mn : "?", pc);
            }
        }
    }

    fclose(f);
    NSLog(@"[dumper] done. wrote /tmp/cm_dump.txt");
}

__attribute__((constructor))
static void entry(void) {
    @autoreleasepool {
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(8 * NSEC_PER_SEC)),
                       dispatch_get_main_queue(), ^{
            dumpEverything();
        });
    }
}
""")

print("done")
