from memory import alloc

fn main():
    var p = alloc[UInt8](1)
    # Force a type error to see the type name
    var i: Int = p
    p.free()
