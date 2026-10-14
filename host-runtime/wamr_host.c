#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "wasm_export.h" // WAMR header

// Example native bridge entry point for your Android app to trigger .wasm execution
__attribute__((visibility("default")))
int execute_wasm_tool(const char* wasm_path, int argc, char** argv) {
    // Initialize WAMR runtime environment
    RuntimeInitArgs init_args;
    memset(&init_args, 0, sizeof(RuntimeInitArgs));
    
    if (!wasm_runtime_full_init(&init_args)) {
        printf("Failed to initialize WAMR engine.\n");
        return -1;
    }

    // Load file bytes into memory buffer
    FILE *f = fopen(wasm_path, "r");
    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    char *buffer = malloc(size);
    fread(buffer, 1, size, f);
    fclose(f);

    char error_buf[128];
    wasm_module_t module = wasm_runtime_load((uint8_t*)buffer, size, error_buf, sizeof(error_buf));
    if (!module) {
        printf("Error loading WASM module: %s\n", error_buf);
        free(buffer);
        return -1;
    }

    wasm_module_inst_t module_inst = wasm_runtime_instantiate(module, 64 * 1024, 64 * 1024, error_buf, sizeof(error_buf));
    if (!module_inst) {
        printf("Error instantiating module: %s\n", error_buf);
        wasm_runtime_unload(module);
        free(buffer);
        return -1;
    }

    // Invoke main function
    wasm_application_execute_main(module_inst, argc, argv);

    // Cleanup
    wasm_runtime_deinstantiate(module_inst);
    wasm_runtime_unload(module);
    free(buffer);
    wasm_runtime_destroy();
    return 0;
}
