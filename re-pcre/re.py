import ffi
import array


pcre = ffi.open("libpcre.so.3")

#       pcre *pcre_compile(const char *pattern, int options,
#            const char **errptr, int *erroffset,
#            const unsigned char *tableptr);
pcre_compile = pcre.func("p", "pcre_compile", "sipps")

#       int pcre_exec(const pcre *code, const pcre_extra *extra,
#            const char *subject, int length, int startoffset,
#            int options, int *ovector, int ovecsize);
pcre_exec = pcre.func("i", "pcre_exec", "ppsiiipi")

#       int pcre_fullinfo(const pcre *code, const pcre_extra *extra,
#            int what, void *where);
pcre_fullinfo = pcre.func("i", "pcre_fullinfo", "ppip")


IGNORECASE = I = 1
MULTILINE = M = 2
DOTALL = S = 4
VERBOSE = X = 8
PCRE_ANCHORED = 0x10

PCRE_INFO_CAPTURECOUNT = 2


class PCREMatch:

    def __init__(self, s, num_matches, offsets):
        self.s = s
        self.num = num_matches
        self.offsets = offsets

    def group(self, n):
        return self.s[self.offsets[n*2]:self.offsets[n*2+1]]

    def span(self, n=0):
        return self.offsets[n*2], self.offsets[n*2+1]


class PCREPattern:

    def __init__(self, compiled_ptn):
        self.obj = compiled_ptn

    def search(self, s, _flags=0):
        buf = bytes(4)
        pcre_fullinfo(self.obj, None, PCRE_INFO_CAPTURECOUNT, buf)
        cap_count = int.from_bytes(buf)
        ov = array.array('i', [0, 0, 0] * (cap_count + 1))
        num = pcre_exec(self.obj, None, s, len(s), 0, _flags, ov, len(ov))
        if num == -1:
            # No match
            return None
        return PCREMatch(s, num, ov)

    def match(self, s):
        return self.search(s, PCRE_ANCHORED)

    def sub(self, repl, s):
        assert "\\" not in repl, "Backrefs not implemented"
        res = ""
        while s:
            m = self.search(s)
            if not m:
                return res + s
            beg, end = m.span()
            res += s[:beg]
            assert not callable(repl)
            res += repl
            s = s[end:]


def compile(pattern, flags=0):
    errptr = bytes(4)
    erroffset = bytes(4)
    regex = pcre_compile(pattern, flags, errptr, erroffset, None)
    assert regex
    return PCREPattern(regex)


def search(pattern, string, flags=0):
    r = compile(pattern, flags)
    return r.search(string)


def sub(pattern, repl, s, count=0, flags=0):
    r = compile(pattern, flags)
    return r.sub(repl, s)