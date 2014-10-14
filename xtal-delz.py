import sys

RING_BUF_SIZE = 4096
NO_COMPRESS_SIZE = 3
MAX_MATCH_LEN = 15 + NO_COMPRESS_SIZE

def decompress(data):
    data = iter(bytearray(data))
    data_idx = 0
    ring_buf = bytearray('\0'*RING_BUF_SIZE)
    ring_buf_idx = 0
    flags = 0
    while True:
        flags >>= 1
        if not (flags & 0x100):
            flags = next(data) | 0xff00
        if flags & 1:
            c = next(data)
            ring_buf[ring_buf_idx] = c; ring_buf_idx = (ring_buf_idx + 1) % RING_BUF_SIZE
            yield c
        else:
            c1 = next(data)
            c2 = next(data)
            pos = c1 | ((c2 & 0xf0) << 4)
            length = (c2 & 0x0f) + NO_COMPRESS_SIZE
            for i in xrange(length):
                c = ring_buf[(i + pos) % RING_BUF_SIZE]
                ring_buf[ring_buf_idx] = c; ring_buf_idx = (ring_buf_idx + 1) % RING_BUF_SIZE
                yield c

indata = open(sys.argv[1], 'rb').read()
indata = indata[4:]
sys.stdout.write(bytearray(decompress(indata)))


