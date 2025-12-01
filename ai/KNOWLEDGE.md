# Knowledge Base

## Mojo Nightly Quirks (v0.26+)

### UnsafePointer & Allocation
**Issue:** `UnsafePointer.alloc` is deprecated. Use global `alloc`.
**Issue:** `UnsafePointer` type inference is strict and brittle in Nightly `0.26.1.dev`.
**Solution:**
1. Use `from memory import alloc`.
2. If strict type matching fails (e.g. `ExternalMutPointer` not exported), cast the pointer to `Int` for storage/passing to FFI.
   ```mojo
   var ptr = alloc[UInt8](10)
   var addr = Int(ptr) # Store as Int
   external_call["c_func", NoneType](addr)
   ```

### Libc Binding
To bind `libc` functions taking pointers, use `Int` (VoidPtr bypass) if `UnsafePointer[NoneType]` causes implicit conversion errors.