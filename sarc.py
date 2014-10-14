# {enemy,fighter,assistpokemon/item_,stage}
import sys, struct, zlib, subprocess, os
print 'Getting strings...'
outdir = sys.argv[3]
if not os.path.exists(outdir):
    os.mkdir(outdir)
strs = subprocess.check_output(['strings', '-', sys.argv[2]]).rstrip().split('\n')
by_crc = {}
def try_crc(str):
    crc = zlib.crc32(str) & 0xffffffff
    by_crc.setdefault(crc, set()).add(str)
for fighter in ['koopa', 'zelda', 'sheik', 'marth', 'gamewatch', 'ganon', 'falco', 'wario', 'metaknight', 'pit', 'szerosuit', 'pikmin', 'diddy', 'dedede', 'ike', 'lucario', 'robot', 'toonlink', 'lizardon', 'sonic', 'purin', 'mariod', 'lucina', 'pitb', 'rosetta', 'wiifit', 'littlemac', 'murabito', 'palutena', 'reflet', 'duckhunt', 'koopajr', 'shulk', 'gekkouga', 'pacman', 'rockman', 'koopag', 'warioman', 'littlemacg', 'lucariom', 'miienemyf', 'miienemys', 'miienemyg']:
    try_crc('fighter/' + fighter)
for stage in '3DLand 3dland Allstar_c AuraHitF AuraHitL AuraHitM AuraHitS BalloonFight BattleField_c Battlefieldk_c Bomb_c Colloseum DxCorneria DxGarden DxZebes ElecHitF ElecHitL ElecHitM ElecHitS End_c FireHitF FireHitL FireHitM FireHitS FzeroSfc Gerudo HitFlash Homerun_c Island Magicant MainField MiniRoom00 MiniRoom01 MiniRoom02 MiniRoom03 MiniRoom05 NewMario2 NintenDogs Nobore None OnlineTraining_c PacMaze Paper Pictchat Plasma Playable_roll_c PrePlay_c Prism ProgTest PunchOut2_c PunchOut_c Pupupuland Pupupuland_VC PurpleFireHitF PurpleFireHitL PurpleFireHitM PurpleFireHitS Race00 Race01 RainbowRoad Rush_c StreetPass Title_c Tomodachi Train Uprising WeakenFlashLv1 WeakenFlashLv2 WeakenFlashLv3 Wily2 XCrayon XGreenhill XGw XMadein XMarioPast XPikmin XenoBlade_c allstar_c balloon_fight battle_field_k_c battlefield_c bomb_c colloseum dx_corneria dx_garden dx_zebes end end_c field_smash fzerosfc gerudo homerun_c island magicant main_field melee miniroom newmario2 nintendogs nobore online_training_c other pacmaze paper pictchat plasma playable_roll_c pre_play_c prism punchout_c pupupuland race rainbowroad rush_c streetpass title_c tomodachi train uprising wily2 x_crayon x_greenhill x_gw x_madein x_mariopast x_pikmin xenoblade_c'.split(' '):
    try_crc('stage/' + stage)
try_crc('menu/menu')
try_crc('minigame/minigame')
for str in strs:
    for prefix in {'', 'enemy/', 'fighter/', 'assistpokemon/item_', 'stage/'}:
        try_crc(prefix + str)


fp = open(sys.argv[1], 'rb')
assert fp.read(4) == 'SARC'
num_files, = struct.unpack('<I', fp.read(4))
for i in xrange(num_files):
    print i
    fp.seek(0x10 + 0x10 * i)
    crc, off, flags, size = struct.unpack('<IIII', fp.read(16))
    fp.seek(off)
    compressed = fp.read(size)
    print hex(flags)
    data = zlib.decompress(compressed)
    strings = by_crc.get(crc, set())
    print strings
    #continue
    if len(strings) >= 2:
        raise Exception('Multiple CRC possibilities for %08x' % crc)
    elif len(strings) == 1:
        fn = strings.pop()
        assert not fn.startswith('/')
        outfn = os.path.join(outdir, fn)
        if not os.path.exists(os.path.dirname(outfn)):
            os.makedirs(os.path.dirname(outfn))
    else:
        outfn = os.path.join(outdir, 'unkcrc-%08x' % crc)
    open(outfn, 'wb').write(data)

