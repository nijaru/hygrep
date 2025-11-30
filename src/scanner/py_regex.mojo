from python import Python, PythonObject

struct Regex:
    var _re: PythonObject
    var _pattern: String

    fn __init__(out self, pattern: String):
        self._pattern = pattern
        # We can't handle exception safely in __init__ without raising, 
        # but for now we assume pattern is valid or let it crash (MVP).
        # Better: lazy init or try/except block if possible.
        self._re = PythonObject(None) 
        try:
            var re = Python.import_module("re")
            # Compile with IgnoreCase (2)
            self._re = re.compile(pattern, 2)
        except:
            print("Failed to compile regex: " + pattern)

    fn __copyinit__(out self, existing: Self):
        self._re = existing._re
        self._pattern = existing._pattern

    fn matches(self, text: String) -> Bool:
        try:
            # Python search returns None if no match
            if not self._re:
                return False
            var m = self._re.search(text)
            if m:
                return True
            return False
        except:
            return False
