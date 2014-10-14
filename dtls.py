import struct, sys, zlib, os
from collections import OrderedDict
from cStringIO import StringIO

dtfn, lsfn, outdir = sys.argv[1:]
dtfp = open(dtfn, 'rb')
lsfp = open(lsfn, 'rb')
lsfp.read(4)
count, = struct.unpack('<I', lsfp.read(4))
dt_offsets = OrderedDict()
dt_total_size = 0
for i in xrange(count):
    crc, start, size = struct.unpack('<III', lsfp.read(12))
    dt_offsets[crc] = (start, size)
    dt_total_size += size
assert lsfp.read(1) == ''

def get_file((start, size)):
    dtfp.seek(start)
    compressed = dtfp.read(size)
    data = compressed
    if compressed.startswith('\xcc\xcc\xcc\xcc'):
        z = compressed.find('\x78\x9c')
        if z != -1 and z <= 0x300:
            decompressed = zlib.decompress(compressed[z:])
            return decompressed, True
    return data, False

def invertify(msg):
    return ''.join(chr(~ord(msg[i]) & 0xff) for i in xrange(4)) + msg[4:]

def stupidcrc(filename):
    return zlib.crc32(invertify(filename)) & 0xffffffff

resource = dt_offsets[stupidcrc('resource')]
resource_data, was_compressed = get_file(resource)
open('/tmp/resource.bin', 'wb').write(resource_data)
assert resource_data.startswith('RF')
offset_to_compressed, = struct.unpack('<I', resource_data[4:8])
rf, hl1, _, hl2, \
_0x18_entries_len, timestamp, compressed_len, decompressed_len, \
start_of_strs_plus, len_strs \
    = struct.unpack('<10I', resource_data[:0x28])

resource_dec = zlib.decompress(resource_data[offset_to_compressed:])
rdfp = StringIO(resource_dec)
open('/tmp/resource.dec', 'wb').write(resource_dec)

rdfp.seek(start_of_strs_plus - hl1)
num_segments, = struct.unpack('<I', rdfp.read(4))
segments = [rdfp.read(0x2000) for seg in xrange(num_segments)]

def get_from_offset(off, len):
    # this is actually just a linear mapping, so pretty useless - but at least
    # this documents what needs to happen for any repackers
    seg_off = off & 0x1fff
    return segments[off / 0x2000][seg_off:seg_off + len]

parts = []
offset_parts = []

known_crcs = set()
resource_total_size = 0

if 1:
    num_offsets, = struct.unpack('<I', rdfp.read(4))
    extension_offsets = struct.unpack('<%dI' % num_offsets, rdfp.read(4 * num_offsets))
    extensions = []
    for i, exto in enumerate(extension_offsets):
        ext = get_from_offset(exto, 64)
        ext = ext[:ext.find('\0')]
        extensions.append(ext)
        #print i, repr(ext)

    rdfp.seek(0)
    num_8sized, = struct.unpack('<I', rdfp.read(4))
    rdfp.read(num_8sized * 8)
    another_size, = struct.unpack('<I', rdfp.read(4))
    rdfp.read(another_size)
    while rdfp.tell() < _0x18_entries_len:
        off_in_chunk, name_offset_etc, cmp_size, dec_size, timestamp, derp1 = struct.unpack('<IIIIII', rdfp.read(0x18))
        ext = name_offset_etc >> 24
        name_offset = name_offset_etc & 0xfffff
        name = get_from_offset(name_offset, 128)
        if name_offset_etc & 0x00800000:
            reference, = struct.unpack('<H', name[:2])
            ref_len = (reference & 0x1f) + 4
            ref_reloff = (reference & 0xe0) >> 6 << 8 | (reference >> 8)
            name = get_from_offset(name_offset - ref_reloff, ref_len) + name[2:]
        if '\0' in name:
            name = name[:name.find('\0')]
        name += extensions[ext]

        nesting_level = derp1 & 0xff
        localized = bool(derp1 & 0x800)
        final = bool(derp1 & 0x400)
        compressed = bool(derp1 & 0x200)
        parts = parts[:nesting_level - 1] + [name]


        path = ''.join(parts)

        if final:
            start, size = None, None
            crc_path = 'data/' + path.rstrip('/') + ('/packed' if compressed else '')
            crc = stupidcrc(crc_path)
            offset = dt_offsets[crc]
        else:
            offset = None
        offset_parts = offset_parts[:nesting_level - 1] + [offset]

        outfn = os.path.join(outdir, path)
        if path.endswith('/'):
            if not os.path.exists(outfn):
                os.mkdir(outfn)
        else:
            for part in offset_parts[::-1]:
                if part is not None:
                    chunk_start, chunk_size = part
                    break
            else:
                raise Exception("%s: nothing to look at" % path)
            assert off_in_chunk + cmp_size <= chunk_size
            dtfp.seek(chunk_start + off_in_chunk)
            cmp_data = dtfp.read(cmp_size)
            # XXX why isn't 'compressed' right?
            if cmp_data.startswith('x\x9c'):
                file_data = zlib.decompress(cmp_data)
            else:
                file_data = cmp_data
            assert len(file_data) == dec_size
            open(outfn, 'wb').write(file_data)


        resource_total_size += cmp_size

if 0:
    for missing in set(dt_offsets.keys()) - known_crcs:
        print 'Missing', missing
