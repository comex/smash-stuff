import sys, struct
fp = open(sys.argv[1], 'rb')
fp.seek(0xc8)
if len(sys.argv) > 2:
    idafp = open(sys.argv[2], 'w')
segment_offset, segment_count = struct.unpack('<II', fp.read(8))
export_offset, export_count = struct.unpack('<II', fp.read(8))
segs = {}
for i in xrange(segment_count):
    fp.seek(segment_offset + i * 12)
    off, size, num = struct.unpack('<III', fp.read(12))
    #print '(%d) %x+%x' % (num, off, size)
    if num in segs:
        continue # ??
    segs[num] = {'off': off, 'size': size}

def get_addr(seg_data):
    seg_num = seg_data & 0xf
    off_in_seg = seg_data >> 4
    seg = segs[seg_num]
    assert off_in_seg < seg['size']
    return seg['off'] + off_in_seg

if 0:
    print '# EXPORTS'
    for i in xrange(export_count):
        fp.seek(export_offset + i * 8)
        name_offset, seg_data = struct.unpack('<II', fp.read(8))
        addr = get_addr(seg_data)
        fp.seek(name_offset)
        name = fp.read(128)
        name = name[:name.find('\0')]
        print name, hex(addr)
        if idafp:
            idafp.write('MakeName(0x%x, "%s")\n' % (addr, name))

if 1:
    print '# IMPORTS'
    if idafp:
        idafp.write('StartImports()\n')
    fp.seek(0x118)
    import_strings_offset, import_strings_size = struct.unpack('<II', fp.read(8))
    for tab in xrange(3):
        fp.seek(0x100 + 8 * tab)
        import_offset, import_count = struct.unpack('<II', fp.read(8))
        print '# table %d: %d entries' % (tab, import_count)
        for i in xrange(import_count):
            fp.seek(import_offset + i * 8)
            name_offset, reloc_offset = struct.unpack('<II', fp.read(8))
            fp.seek(name_offset)
            name = fp.read(128)
            name = name[:name.find('\0')]
            print '%s:' % name
            fp.seek(reloc_offset)
            while True:
                seg_data, patch_type, is_last, u1, u2, u3 = struct.unpack('<IBBBBI', fp.read(12))
                addr = get_addr(seg_data)
                print '   -> %x (%d)' % (addr, patch_type)
                if idafp and patch_type == 2:
                    idafp.write('MakeName(0x%x, "%s")\n' % (addr, name))
                    idafp.write('DoImport(0x%x)\n' % (addr,))
                if is_last:
                    break


