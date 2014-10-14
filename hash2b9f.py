def hash2b9f(s):
    s = bytearray(s)
    val = 0x12dd273
    l = len(s)
    if l > 1:
        idx = 0
        if l % 2 == 0:
            val = s[idx] ^ 0x2b9f6a9f
            idx += 1
        while idx < l - 1:
            val = (37 * (s[idx] ^ (37 * val))) & 0xffffffff
            val ^= s[idx+1]
            idx += 2
    if l >= 1:
        val = (s[-1] ^ (37 * val)) & 0xffffffff
    return val

print hex(hash2b9f('param/game/camera_boss.bin'))

#print map(hex, map(hash2b9f, ['abcde', 'ab', 'a', '']))
