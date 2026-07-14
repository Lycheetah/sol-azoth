/**
 * BOOT SCENE — Procedural pixel art generation
 * Creates all sprites/textures at boot time.
 * No external assets needed — everything is drawn in code.
 *
 * Palette: Lycheetah signature — gold, cyan, violet, dark parchment
 */
export class BootScene extends Phaser.Scene {
    constructor() {
        super({ key: 'BootScene' });
    }

    preload() {
        // Show loading bar
        const w = this.cameras.main.width;
        const h = this.cameras.main.height;

        const barBg = this.add.rectangle(w / 2, h / 2, 320, 20, 0x1a1818);
        const bar = this.add.rectangle(w / 2 - 158, h / 2, 0, 16, 0xf0c040);
        bar.setOrigin(0, 0.5);

        const loadText = this.add.text(w / 2, h / 2 - 30, 'FORGING THE LONG LIGHT...', {
            fontFamily: 'monospace',
            fontSize: '14px',
            color: '#f0c040',
            align: 'center'
        }).setOrigin(0.5);

        this.load.on('progress', (v) => {
            bar.width = 316 * v;
        });

        this.load.on('complete', () => {
            barBg.destroy();
            bar.destroy();
            loadText.destroy();
        });

        // Load a tiny dummy asset to trigger the progress bar
        // (we generate everything procedurally in create())
        this.load.image('__dummy__',
            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        );
    }

    create() {
        this.generateTextures();
        this.scene.start('GameScene');
    }

    /**
     * Generate all game textures procedurally using Phaser graphics
     */
    generateTextures() {
        this.generateSeeker();
        this.generateEnemies();
        this.generateProjectiles();
        this.generateTiles();
        this.generateItems();
        this.generateEffects();
        this.generateUI();
    }

    /* ─── SEEKER SPRITE (32×48, top-down view) ─── */
    generateSeeker() {
        const g = this.make.graphics({ add: false });

        // Shadow
        g.fillStyle(0x000000, 0.3);
        g.fillEllipse(16, 44, 20, 6);

        // Body — dark robe with gold trim
        g.fillStyle(0x1a1a2e);
        g.fillRect(10, 16, 12, 20); // torso

        // Gold trim
        g.fillStyle(0xf0c040);
        g.fillRect(10, 16, 12, 2);  // collar
        g.fillRect(10, 32, 12, 1);  // belt

        // Head
        g.fillStyle(0xe8d5b7);
        g.fillCircle(16, 10, 7);

        // Hair
        g.fillStyle(0x2a1a0a);
        g.fillRect(11, 3, 10, 5);

        // Eyes
        g.fillStyle(0xf0c040);
        g.fillRect(13, 9, 2, 2);
        g.fillRect(17, 9, 2, 2);

        // Arms
        g.fillStyle(0x1a1a2e);
        g.fillRect(6, 18, 4, 12);
        g.fillRect(22, 18, 4, 12);

        // Hands
        g.fillStyle(0xe8d5b7);
        g.fillRect(6, 28, 4, 3);
        g.fillRect(22, 28, 4, 3);

        // Legs
        g.fillStyle(0x2a1a1a);
        g.fillRect(11, 36, 5, 8);
        g.fillRect(16, 36, 5, 8);

        // Feet
        g.fillStyle(0x3a2a1a);
        g.fillRect(10, 44, 6, 3);
        g.fillRect(16, 44, 6, 3);

        g.generateTexture('seeker', 32, 48);
        g.destroy();

        // Walk animation frames (simple variants)
        for (let frame = 0; frame < 4; frame++) {
            const gf = this.make.graphics({ add: false });
            gf.copy(g, 0, 0);

            // Slight leg offset per frame
            const legOffset = [0, 1, 0, -1][frame];
            gf.fillStyle(0x2a1a1a);
            gf.fillRect(11 + legOffset, 36, 5, 8);
            gf.fillRect(16 - legOffset, 36, 5, 8);
            gf.fillStyle(0x3a2a1a);
            gf.fillRect(10 + legOffset, 44, 6, 3);
            gf.fillRect(16 - legOffset, 44, 6, 3);

            gf.generateTexture(`seeker_walk_${frame}`, 32, 48);
            gf.destroy();
        }
    }

    /* ─── ENEMIES ─── */
    generateEnemies() {
        // OVERCLAIMER — floating eye with too many rings
        const oc = this.make.graphics({ add: false });
        oc.fillStyle(0x8b0000, 0.4);
        oc.fillCircle(16, 16, 16);
        oc.fillStyle(0x8b0000, 0.6);
        oc.fillCircle(16, 16, 12);
        oc.fillStyle(0xcc0000);
        oc.fillCircle(16, 16, 8);
        oc.fillStyle(0xff0000);
        oc.fillCircle(16, 16, 4);
        oc.fillStyle(0xffffff);
        oc.fillCircle(14, 14, 2);
        oc.fillStyle(0x000000);
        oc.fillCircle(15, 15, 1);
        oc.generateTexture('overclaimer', 32, 32);
        oc.destroy();

        // HALF-MADE — shifting amorphous shape
        const hm = this.make.graphics({ add: false });
        hm.fillStyle(0x4a4a6a, 0.6);
        hm.fillCircle(16, 16, 14);
        hm.fillStyle(0x6a6a8a, 0.4);
        hm.fillCircle(16, 14, 10);
        hm.fillStyle(0x8a8aaa, 0.3);
        hm.fillCircle(16, 18, 6);
        hm.fillStyle(0xaaaacc, 0.2);
        hm.fillCircle(12, 12, 4);
        hm.fillStyle(0xccccff, 0.1);
        hm.fillCircle(20, 14, 3);
        hm.generateTexture('halfmade', 32, 32);
        hm.destroy();

        // THE LOOP — spiral
        const lp = this.make.graphics({ add: false });
        lp.lineStyle(2, 0x00ff88, 0.8);
        for (let i = 0; i < 360; i += 15) {
            const r = 2 + (i / 360) * 12;
            const x = 16 + Math.cos(i * Math.PI / 180) * r;
            const y = 16 + Math.sin(i * Math.PI / 180) * r;
            lp.fillStyle(0x00ff88, 0.5);
            lp.fillCircle(x, y, 1.5);
        }
        lp.generateTexture('loop', 32, 32);
        lp.destroy();

        // SHADE — basic shadow enemy
        const sh = this.make.graphics({ add: false });
        sh.fillStyle(0x1a1a2e, 0.8);
        sh.fillCircle(16, 16, 12);
        sh.fillStyle(0x2a2a4e, 0.6);
        sh.fillCircle(16, 16, 8);
        sh.fillStyle(0x3a3a5e, 0.4);
        sh.fillCircle(16, 16, 4);
        sh.fillStyle(0xff4444, 0.8);
        sh.fillCircle(16, 16, 2);
        sh.generateTexture('shade', 32, 32);
        sh.destroy();
    }

    /* ─── PROJECTILES ─── */
    generateProjectiles() {
        // Insight ray (player attack)
        const ir = this.make.graphics({ add: false });
        ir.fillStyle(0xf0c040, 0.9);
        ir.fillCircle(4, 4, 4);
        ir.fillStyle(0xffffff, 0.5);
        ir.fillCircle(4, 4, 2);
        ir.generateTexture('insight_ray', 8, 8);
        ir.destroy();

        // Enemy projectile
        const ep = this.make.graphics({ add: false });
        ep.fillStyle(0xff2222, 0.8);
        ep.fillCircle(4, 4, 3);
        ep.fillStyle(0xff6666, 0.4);
        ep.fillCircle(4, 4, 2);
        ep.generateTexture('enemy_bolt', 8, 8);
        ep.destroy();

        // Measure glyph (skill 1)
        const mg = this.make.graphics({ add: false });
        mg.lineStyle(2, 0x00ccff, 1);
        mg.strokeCircle(8, 8, 6);
        mg.lineStyle(1, 0x00ccff, 0.8);
        mg.strokeCircle(8, 8, 3);
        mg.fillStyle(0x00ccff, 0.3);
        mg.fillCircle(8, 8, 2);
        mg.generateTexture('measure_glyph', 16, 16);
        mg.destroy();

        // Compress glyph (skill 2)
        const cg = this.make.graphics({ add: false });
        cg.fillStyle(0xff6600, 0.8);
        cg.fillCircle(8, 8, 7);
        cg.fillStyle(0xffaa00, 0.6);
        cg.fillCircle(8, 8, 4);
        cg.fillStyle(0xffffff, 0.4);
        cg.fillCircle(8, 8, 2);
        cg.generateTexture('compress_glyph', 16, 16);
        cg.destroy();

        // Transmute glyph (skill 3)
        const tg = this.make.graphics({ add: false });
        tg.fillStyle(0x00ff88, 0.5);
        tg.fillCircle(8, 8, 7);
        tg.lineStyle(2, 0x00ff88, 1);
        const pts = [];
        for (let i = 0; i < 5; i++) {
            const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
            pts.push({ x: 8 + Math.cos(a) * 6, y: 8 + Math.sin(a) * 6 });
        }
        tg.strokePoints(pts, true);
        tg.generateTexture('transmute_glyph', 16, 16);
        tg.destroy();

        // Break glyph (skill 4)
        const bg = this.make.graphics({ add: false });
        bg.fillStyle(0xcc44ff, 0.7);
        bg.fillRect(2, 2, 12, 12);
        bg.fillStyle(0xee88ff, 0.5);
        bg.fillRect(4, 4, 8, 8);
        bg.fillStyle(0xffffff, 0.3);
        bg.fillRect(6, 6, 4, 4);
        bg.generateTexture('break_glyph', 16, 16);
        bg.destroy();
    }

    /* ─── TILES ─── */
    generateTiles() {
        const tileSize = 32;

        // Floor tile — dark stone
        const fl = this.make.graphics({ add: false });
        fl.fillStyle(0x1a1818);
        fl.fillRect(0, 0, 32, 32);
        fl.lineStyle(1, 0x2a2828, 0.3);
        fl.strokeRect(0, 0, 32, 32);
        // Random crack details
        fl.lineStyle(1, 0x2a2020, 0.2);
        fl.lineBetween(5, 8, 12, 8);
        fl.lineBetween(20, 22, 28, 22);
        fl.generateTexture('floor', 32, 32);
        fl.destroy();

        // Wall tile — dark brick
        const wl = this.make.graphics({ add: false });
        wl.fillStyle(0x2a2222);
        wl.fillRect(0, 0, 32, 32);
        wl.lineStyle(1, 0x3a3232, 0.4);
        // Brick pattern
        wl.strokeRect(0, 0, 16, 10);
        wl.strokeRect(16, 0, 16, 10);
        wl.strokeRect(4, 10, 12, 10);
        wl.strokeRect(20, 10, 12, 10);
        wl.strokeRect(0, 20, 16, 12);
        wl.strokeRect(16, 20, 16, 12);
        // Gold vein
        wl.lineStyle(1, 0xf0c040, 0.15);
        wl.lineBetween(0, 15, 32, 15);
        wl.generateTexture('wall', 32, 32);
        wl.destroy();

        // Door tile
        const dr = this.make.graphics({ add: false });
        dr.fillStyle(0x3a2a1a);
        dr.fillRect(4, 0, 24, 32);
        dr.fillStyle(0x4a3a2a);
        dr.fillRect(6, 2, 20, 28);
        dr.lineStyle(1, 0xf0c040, 0.5);
        dr.strokeRect(6, 2, 20, 28);
        dr.fillStyle(0xf0c040, 0.6);
        dr.fillCircle(22, 16, 2);
        dr.generateTexture('door', 32, 32);
        dr.destroy();

        // Shrine tile
        const sh = this.make.graphics({ add: false });
        sh.fillStyle(0x1a1a2e);
        sh.fillRect(4, 8, 24, 24);
        sh.fillStyle(0x2a2a4e);
        sh.fillRect(6, 10, 20, 20);
        // Glow effect
        sh.fillStyle(0xf0c040, 0.2);
        sh.fillCircle(16, 16, 10);
        sh.fillStyle(0xf0c040, 0.4);
        sh.fillCircle(16, 16, 5);
        sh.fillStyle(0xffffff, 0.3);
        sh.fillCircle(16, 16, 2);
        sh.generateTexture('shrine', 32, 32);
        sh.destroy();

        // Exit stairs
        const ex = this.make.graphics({ add: false });
        ex.fillStyle(0x2a1a0a);
        ex.fillRect(4, 0, 24, 32);
        for (let i = 0; i < 5; i++) {
            ex.fillStyle(0x4a3a2a, 0.5 + i * 0.1);
            ex.fillRect(6 + i * 2, 2 + i * 6, 20 - i * 4, 4);
        }
        ex.fillStyle(0xf0c040, 0.3);
        ex.fillCircle(16, 16, 6);
        ex.generateTexture('stairs', 32, 32);
        ex.destroy();
    }

    /* ─── ITEMS ─── */
    generateItems() {
        // Glyph shard
        const gs = this.make.graphics({ add: false });
        gs.fillStyle(0xf0c040, 0.8);
        gs.fillTriangle(8, 2, 2, 14, 14, 14);
        gs.fillStyle(0xffdd88, 0.6);
        gs.fillTriangle(8, 4, 4, 12, 12, 12);
        gs.fillStyle(0xffffff, 0.4);
        gs.fillCircle(8, 8, 2);
        gs.generateTexture('glyph_shard', 16, 16);
        gs.destroy();

        // Health vial
        const hv = this.make.graphics({ add: false });
        hv.fillStyle(0x00ff88, 0.7);
        hv.fillRect(5, 6, 6, 10);
        hv.fillStyle(0x00ff88, 0.5);
        hv.fillRect(5, 2, 6, 4);
        hv.fillStyle(0x44ffaa, 0.4);
        hv.fillRect(7, 8, 2, 6);
        hv.generateTexture('health_vial', 16, 16);
        hv.destroy();

        // Light essence
        const le = this.make.graphics({ add: false });
        le.fillStyle(0xf0c040, 0.3);
        le.fillCircle(8, 8, 8);
        le.fillStyle(0xf0c040, 0.5);
        le.fillCircle(8, 8, 5);
        le.fillStyle(0xffffff, 0.6);
        le.fillCircle(8, 8, 2);
        le.generateTexture('light_essence', 16, 16);
        le.destroy();
    }

    /* ─── EFFECTS ─── */
    generateEffects() {
        // Explosion particle
        const ex = this.make.graphics({ add: false });
        ex.fillStyle(0xff6600, 0.8);
        ex.fillCircle(4, 4, 4);
        ex.fillStyle(0xffaa00, 0.5);
        ex.fillCircle(4, 4, 2);
        ex.generateTexture('particle', 8, 8);
        ex.destroy();

        // Sparkle
        const sp = this.make.graphics({ add: false });
        sp.fillStyle(0xf0c040, 0.9);
        sp.fillRect(3, 0, 2, 8);
        sp.fillRect(0, 3, 8, 2);
        sp.fillCircle(4, 4, 2);
        sp.generateTexture('sparkle', 8, 8);
        sp.destroy();

        // Damage number background
        const dn = this.make.graphics({ add: false });
        dn.fillStyle(0x000000, 0.5);
        dn.fillRect(0, 0, 20, 10);
        dn.generateTexture('dmg_bg', 20, 10);
        dn.destroy();
    }

    /* ─── UI TEXTURES ─── */
    generateUI() {
        // Skill slot background
        const ss = this.make.graphics({ add: false });
        ss.fillStyle(0x1a1818, 0.8);
        ss.fillRect(0, 0, 40, 40);
        ss.lineStyle(1, 0xf0c040, 0.4);
        ss.strokeRect(0, 0, 40, 40);
        ss.generateTexture('skill_slot', 40, 40);
        ss.destroy();

        // Skill slot active
        const sa = this.make.graphics({ add: false });
        sa.fillStyle(0x1a1818, 0.9);
        sa.fillRect(0, 0, 40, 40);
        sa.lineStyle(2, 0xf0c040, 0.9);
        sa.strokeRect(0, 0, 40, 40);
        sa.generateTexture('skill_slot_active', 40, 40);
        sa.destroy();

        // Skill slot cooldown
        const sc = this.make.graphics({ add: false });
        sc.fillStyle(0x1a1818, 0.9);
        sc.fillRect(0, 0, 40, 40);
        sc.lineStyle(1, 0x444444, 0.6);
        sc.strokeRect(0, 0, 40, 40);
        sc.generateTexture('skill_slot_cd', 40, 40);
        sc.destroy();

        // Mini heart for HP bar
        const hh = this.make.graphics({ add: false });
        hh.fillStyle(0xff2244, 0.8);
        hh.fillCircle(4, 3, 3);
        hh.fillCircle(8, 3, 3);
        hh.fillTriangle(1, 4, 11, 4, 6, 10);
        hh.generateTexture('heart', 12, 12);
        hh.destroy();

        // XP star
        const xs = this.make.graphics({ add: false });
        xs.fillStyle(0xf0c040, 0.8);
        const cx = 6, cy = 6;
        for (let i = 0; i < 5; i++) {
            const outerA = (i / 5) * Math.PI * 2 - Math.PI / 2;
            const innerA = outerA + Math.PI / 5;
            const ox = cx + Math.cos(outerA) * 5;
            const oy = cy + Math.sin(outerA) * 5;
            const ix = cx + Math.cos(innerA) * 2;
            const iy = cy + Math.sin(innerA) * 2;
            const nextOuterA = ((i + 1) / 5) * Math.PI * 2 - Math.PI / 2;
            const nox = cx + Math.cos(nextOuterA) * 5;
            const noy = cy + Math.sin(nextOuterA) * 5;
            xs.fillTriangle(cx, cy, ox, oy, ix, iy);
            xs.fillTriangle(cx, cy, ix, iy, nox, noy);
        }
        xs.generateTexture('xp_star', 12, 12);
        xs.destroy();
    }
}
