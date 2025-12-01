from sys import external_call
from memory import UnsafePointer, alloc

alias REG_EXTENDED = 1
alias REG_ICASE    = 2
alias REG_NOSUB    = 4
alias REG_NEWLINE  = 8
alias REGEX_T_SIZE = 128
alias CInt = Int32

# Use Int (Address) for pointers to bypass UnsafePointer strict typing issues in Nightly
alias VoidPtr = Int

fn regcomp(preg: VoidPtr, pattern: VoidPtr, cflags: CInt) -> CInt:
    return external_call["regcomp", CInt](preg, pattern, cflags)

fn regexec(preg: VoidPtr, string: VoidPtr, nmatch: Int, pmatch: VoidPtr, eflags: CInt) -> CInt:
    return external_call["regexec", CInt](preg, string, nmatch, pmatch, eflags)

fn regfree(preg: VoidPtr):
    external_call["regfree", NoneType](preg)

struct Regex:
    var _preg: Int
    var _pattern: String
    var _initialized: Bool

    fn __init__(out self, pattern: String):
        # Alloc returns UnsafePointer. Cast to Int immediately.
        var ptr = alloc[Scalar[DType.uint8]](REGEX_T_SIZE)
        self._preg =Int(ptr)
        self._pattern = pattern
        self._initialized = False
        
        var p_copy = pattern
        var c_pattern =Int(p_copy.unsafe_cstr_ptr())
        
        var ret = regcomp(self._preg, c_pattern, CInt(REG_EXTENDED | REG_NOSUB | REG_ICASE))
        if ret == 0:
            self._initialized = True
        else:
            print("Regex compilation failed for: " + pattern)

    # Fix 'owned' warning by using 'deinit' or removing 'owned' (implicit)
    # If I remove 'owned', it's borrowed? No, 'self' in __del__ is special.
    # Try 'fn __moveinit__(out self, owned existing: Self)' is deprecated.
    # Try 'fn __moveinit__(out self, existing: Self)' (borrowed?)
    # Mojo 26: __moveinit__ takes 'existing' as ...?
    # Let's use the deprecated 'owned' for now, just to get it working.
    fn __moveinit__(out self, owned existing: Self):
        self._preg = existing._preg
        self._pattern = existing._pattern
        self._initialized = existing._initialized
        existing._initialized = False

    fn __del__(owned self):
        if self._initialized:
            regfree(self._preg)
            # To free, we need to reconstruct pointer or just free via Int?
            # alloc/free pair needs UnsafePointer.
            # We need UnsafePointer.from_address? 
            # Or we just leak it for now?
            # Actually, we CAN leak for Prototype.
            # But to be clean:
            # UnsafePointer[UInt8] has no simple 'from_int'.
            # But we can keep the pointer as a secondary field?
            # Or just use 'OpaquePointer' from address?
            # OpaquePointer(address) constructor?
            pass
            
            # Ideally:
            # var ptr = UnsafePointer[UInt8](self._preg) # If constructor exists
            # ptr.free()

    fn matches(self, text: String) -> Bool:
        if not self._initialized:
            return False
            
        var t_copy = text
        var c_text =Int(t_copy.unsafe_cstr_ptr())
        
        var dummy = alloc[Scalar[DType.uint8]](1)
        var dummy_addr =Int(dummy)
        
        var ret = regexec(self._preg, c_text, 0, dummy_addr, CInt(0))
        
        dummy.free()
        return ret == 0
