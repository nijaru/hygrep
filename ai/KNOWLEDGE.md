# Knowledge Base

## Mojo Nightly Quirks (v0.26+)

### UnsafePointer & Allocation
**Issue:** `UnsafePointer.alloc` is deprecated/removed.
**Solution:** Use global `alloc` from `memory`.

```mojo
from memory import UnsafePointer, alloc

fn example():
    # Old: var p = UnsafePointer[Int].alloc(10)
    # New:
    var p = alloc[Int](10)
    p[0] = 1
    p.free()
```

### Libc Binding
To bind `libc` functions taking pointers:
```mojo
alias VoidPtr = UnsafePointer[Scalar[DType.uint8]]
# Pass `ptr` directly.
```
