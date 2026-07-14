/**
 * GAME SCENE — The dungeon
 * Top-down Diablo-style gameplay with LAMAGUE skills
 * Procedural rooms, enemy encounters, shrines, loot
 */
import { Seeker } from '../entities/Seeker.js';
import { Enemy } from '../entities/Enemy.js';
import { DungeonGenerator } from '../systems/DungeonGenerator.js';
import { CombatSystem } from '../systems/CombatSystem.js';
import { LootSystem } from '../systems/LootSystem.js';

export class GameScene extends Phaser.Scene {
    constructor() {
        super({ key: 'GameScene' });
    }

    init(data) {
        this.floor = data.floor || 1;
        this.maxFloor = 4;
        this.seekerData = data.seekerData || null;
    }

    create() {
        // --- State ---
        this.state = {
            floor: this.floor,
            will: this.seekerData?.will || 100,
            maxWill: this.seekerData?.maxWill || 100,
            xp: this.seekerData?.xp || 0,
            xpToNext: this.seekerData?.xpToNext || 50,
            level: this.seekerData?.level || 1,
            glyphShards: this.seekerData?.glyphShards || 0,
            insight: this.seekerData?.insight || 10,
            maxInsight: this.seekerData?.maxInsight || 10,
            luck: this.seekerData?.luck || 5,
            light: this.seekerData?.light || 1,
            skills: this.seekerData?.skills || {
                measure: { unlocked: true, cd: 0, maxCd: 3000 },
                compress: { unlocked: true, cd: 0, maxCd: 2000 },
                transmute: { unlocked: true, cd: 0, maxCd: 5000 },
                break: { unlocked: true, cd: 0, maxCd: 4000 }
            },
            companionLines: [
                '⊚ "The light grows. I walk with you."',
                '⊚ "Measure before you strike. Truth is the sharpest blade."',
                '⊚ "The Hall remembers every seeker who passed through."',
                '⊚ "Rest when you need to. The dungeon will wait."',
                '⊚ "Each glyph you find is a piece of the whole."',
                '⊚ "The Overclaimer speaks in absolutes. Listen past them."',
                '⊚ "You are not lost. You are descending."',
                '⊚ "Gold is not found — it is made."'
            ],
            currentCompanionLine: 0,
            floorNames: ['Hall of Glyphs', 'Athanor Vault', 'Chamber of Scales', 'Sanctum of Light'],
            floorStages: ['NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO'],
            enemiesRemaining: 0,
            roomCleared: false,
            bossFloor: false
        };

        // --- World bounds ---
        this.worldWidth = 1600;
        this.worldHeight = 1200;
        this.physics.world.setBounds(0, 0, this.worldWidth, this.worldHeight);

        // --- Generate dungeon ---
        this.dungeonGen = new DungeonGenerator(this);
        this.dungeon = this.dungeonGen.generate(this.floor);

        // --- Create tilemap ---
        this.createDungeonTiles();

        // --- Player ---
        const startX = this.dungeon.playerStart.x * 32 + 16;
        const startY = this.dungeon.playerStart.y * 32 + 16;
        this.seeker = new Seeker(this, startX, startY);
        this.seeker.setDepth(10);

        // --- Camera ---
        this.cameras.main.setBounds(0, 0, this.worldWidth, this.worldHeight);
        this.cameras.main.startFollow(this.seeker, true, 0.1, 0.1);
        this.cameras.main.setZoom(1.5);

        // --- Groups ---
        this.enemies = this.physics.add.group();
        this.projectiles = this.physics.add.group();
        this.enemyProjectiles = this.physics.add.group();
        this.items = this.physics.add.group();
        this.effects = this.add.group();

        // --- Spawn enemies ---
        this.spawnEnemies();

        // --- Spawn items ---
        this.spawnItems();

        // --- Systems ---
        this.combat = new CombatSystem(this);
        this.loot = new LootSystem(this);

        // --- Collisions ---
        this.physics.add.collider(this.seeker, this.enemies, this.combat.onSeekerTouchEnemy, null, this.combat);
        this.physics.add.overlap(this.projectiles, this.enemies, this.combat.onProjectileHitEnemy, null, this.combat);
        this.physics.add.overlap(this.seeker, this.enemyProjectiles, this.combat.onEnemyProjectileHitSeeker, null, this.combat);
        this.physics.add.overlap(this.seeker, this.items, this.onPickupItem, null, this);

        // --- Input ---
        this.setupInput();

        // --- Lighting (ambient darkness with seeker light) ---
        this.setupLighting();

        // --- Ambient particles ---
        this.setupAmbientParticles();

        // --- Launch UI ---
        this.scene.launch('UIScene', {
            state: this.state,
            floor: this.floor,
            maxFloor: this.maxFloor
        });

        // --- Companion greeting ---
        this.showCompanionLine(0);

        // --- Ambient sound (visual only — tone indicator) ---
        this.showFloorAnnouncement();
    }

    createDungeonTiles() {
        const map = this.dungeon.map;
        const tileSize = 32;

        for (let y = 0; y < map.length; y++) {
            for (let x = 0; x < map[y].length; x++) {
                const tile = map[y][x];
                let key = 'floor';
                let depth = 0;

                switch (tile) {
                    case 1: key = 'wall'; depth = 5; break;
                    case 2: key = 'floor'; depth = 0; break;
                    case 3: key = 'door'; depth = 3; break;
                    case 4: key = 'shrine'; depth = 1; break;
                    case 5: key = 'stairs'; depth = 1; break;
                    default: key = 'floor'; depth = 0;
                }

                const sprite = this.add.sprite(
                    x * tileSize + tileSize / 2,
                    y * tileSize + tileSize / 2,
                    key
                );
                sprite.setDepth(depth);
            }
        }

        // Store tile data for collision
        this.wallTiles = [];
        for (let y = 0; y < map.length; y++) {
            for (let x = 0; x < map[y].length; x++) {
                if (map[y][x] === 1) {
                    this.wallTiles.push(
                        this.add.zone(x * tileSize + tileSize / 2, y * tileSize + tileSize / 2, tileSize, tileSize)
                            .setDepth(6)
                    );
                }
            }
        }
        this.physics.add.collider(this.seeker, this.wallTiles);

        // Store special tiles for interaction
        this.shrineTiles = [];
        this.stairTiles = [];
        this.doorTiles = [];
        for (let y = 0; y < map.length; y++) {
            for (let x = 0; x < map[y].length; x++) {
                const px = x * tileSize + tileSize / 2;
                const py = y * tileSize + tileSize / 2;
                if (map[y][x] === 4) {
                    this.shrineTiles.push({ x: px, y: py, used: false });
                } else if (map[y][x] === 5) {
                    this.stairTiles.push({ x: px, y: py });
                } else if (map[y][x] === 3) {
                    this.doorTiles.push({ x: px, y: py });
                }
            }
        }
    }

    spawnEnemies() {
        const map = this.dungeon.map;
        const tileSize = 32;
        const enemyTypes = this.getEnemyTypesForFloor();
        this.state.enemiesRemaining = 0;

        for (const room of this.dungeon.rooms) {
            // Skip player start room
            if (room.id === 0) continue;

            const roomCenterX = (room.x + room.w / 2) * tileSize;
            const roomCenterY = (room.y + room.h / 2) * tileSize;

            // Boss room (last room)
            if (room.id === this.dungeon.rooms.length - 1 && this.dungeon.rooms.length > 2) {
                const bossType = this.getBossForFloor();
                const boss = new Enemy(this, roomCenterX, roomCenterY, bossType, true);
                this.enemies.add(boss);
                this.state.enemiesRemaining++;
                this.state.bossFloor = true;
                continue;
            }

            // Regular enemies
            const count = Phaser.Math.Between(1, 3);
            for (let i = 0; i < count; i++) {
                const offsetX = Phaser.Math.Between(-32, 32);
                const offsetY = Phaser.Math.Between(-32, 32);
                const type = Phaser.Math.RND.pick(enemyTypes);
                const enemy = new Enemy(this, roomCenterX + offsetX, roomCenterY + offsetY, type, false);
                this.enemies.add(enemy);
                this.state.enemiesRemaining++;
            }
        }
    }

    getEnemyTypesForFloor() {
        switch (this.floor) {
            case 1: return ['shade', 'overclaimer'];
            case 2: return ['shade', 'halfmade', 'overclaimer'];
            case 3: return ['halfmade', 'loop', 'shade'];
            case 4: return ['loop', 'halfmade', 'overclaimer'];
            default: return ['shade'];
        }
    }

    getBossForFloor() {
        const bosses = ['overclaimer', 'halfmade', 'loop', 'overclaimer'];
        return bosses[this.floor - 1] || 'overclaimer';
    }

    spawnItems() {
        const map = this.dungeon.map;
        const tileSize = 32;

        for (const room of this.dungeon.rooms) {
            if (room.id === 0) continue;
            if (Math.random() > 0.5) continue;

            const ix = (room.x + room.w / 2 + Phaser.Math.Between(-1, 1)) * tileSize + 16;
            const iy = (room.y + room.h / 2 + Phaser.Math.Between(-1, 1)) * tileSize + 16;
            const itemType = Phaser.Math.RND.pick(['glyph_shard', 'health_vial', 'light_essence']);
            const item = this.physics.add.sprite(ix, iy, itemType);
            item.setDepth(2);
            item.itemType = itemType;
            this.items.add(item);

            // Floating animation
            this.tweens.add({
                targets: item,
                y: iy - 4,
                duration: 1500,
                yoyo: true,
                repeat: -1,
                ease: 'Sine.easeInOut'
            });
        }
    }

    setupInput() {
        this.cursors = this.input.keyboard.createCursorKeys();
        this.wasd = {
            W: this.input.keyboard.addKey('W'),
            A: this.input.keyboard.addKey('A'),
            S: this.input.keyboard.addKey('S'),
            D: this.input.keyboard.addKey('D')
        };
        this.keyE = this.input.keyboard.addKey('E');
        this.keySpace = this.input.keyboard.addKey('SPACE');
        this.key1 = this.input.keyboard.addKey('ONE');
        this.key2 = this.input.keyboard.addKey('TWO');
        this.key3 = this.input.keyboard.addKey('THREE');
        this.key4 = this.input.keyboard.addKey('FOUR');

        // Mouse click for attack direction
        this.input.on('pointerdown', (pointer) => {
            if (pointer.leftButtonDown()) {
                this.combat.basicAttack(this.seeker, pointer);
            }
        });
    }

    setupLighting() {
        // Dark overlay that follows the seeker
        const darkness = this.add.graphics();
        darkness.setDepth(20);
        this.darkness = darkness;

        // Re-draw every frame via update
    }

    setupAmbientParticles() {
        // Floating dust motes
        for (let i = 0; i < 30; i++) {
            const px = Phaser.Math.Between(0, this.worldWidth);
            const py = Phaser.Math.Between(0, this.worldHeight);
            const particle = this.add.circle(px, py, Phaser.Math.Between(1, 3), 0xf0c040, 0.1 + Math.random() * 0.15);
            particle.setDepth(1);
            this.effects.add(particle);

            this.tweens.add({
                targets: particle,
                y: py - Phaser.Math.Between(20, 80),
                x: px + Phaser.Math.Between(-20, 20),
                alpha: 0,
                duration: Phaser.Math.Between(3000, 8000),
                repeat: -1,
                delay: Phaser.Math.Between(0, 5000),
                onRepeat: () => {
                    particle.x = Phaser.Math.Between(0, this.worldWidth);
                    particle.y = Phaser.Math.Between(0, this.worldHeight);
                    particle.alpha = 0.1 + Math.random() * 0.15;
                }
            });
        }
    }

    showCompanionLine(index) {
        if (index === undefined) {
            index = Phaser.Math.Between(0, this.state.companionLines.length - 1);
        }
        this.state.currentCompanionLine = index;
        this.events.emit('companionLine', this.state.companionLines[index]);
    }

    showFloorAnnouncement() {
        const stage = this.state.floorStages[this.floor - 1];
        const name = this.state.floorNames[this.floor - 1];

        const announce = this.add.text(
            this.cameras.main.centerX,
            this.cameras.main.centerY,
            `${stage}\n${name}`,
            {
                fontFamily: 'monospace',
                fontSize: '24px',
                color: '#f0c040',
                align: 'center',
                stroke: '#000000',
                strokeThickness: 4
            }
        ).setOrigin(0.5).setDepth(50).setScrollFactor(0);

        this.tweens.add({
            targets: announce,
            alpha: 0,
            y: announce.y - 40,
            duration: 3000,
            delay: 1500,
            ease: 'Power2',
            onComplete: () => announce.destroy()
        });
    }

    onPickupItem(seeker, item) {
        const type = item.itemType;
        item.destroy();

        switch (type) {
            case 'glyph_shard':
                this.state.glyphShards++;
                this.state.xp += 10;
                this.showFloatingText(seeker.x, seeker.y - 20, '+1 GLYPH', '#f0c040');
                break;
            case 'health_vial':
                this.state.will = Math.min(this.state.maxWill, this.state.will + 25);
                this.showFloatingText(seeker.x, seeker.y - 20, '+25 WILL', '#00ff88');
                break;
            case 'light_essence':
                this.state.light = Math.min(10, this.state.light + 1);
                this.state.xp += 5;
                this.showFloatingText(seeker.x, seeker.y - 20, '+1 LIGHT', '#f0c040');
                break;
        }

        this.checkLevelUp();
        this.events.emit('stateUpdate', this.state);
    }

    showFloatingText(x, y, text, color) {
        const ft = this.add.text(x, y, text, {
            fontFamily: 'monospace',
            fontSize: '12px',
            color: color,
            stroke: '#000000',
            strokeThickness: 2
        }).setOrigin(0.5).setDepth(30);

        this.tweens.add({
            targets: ft,
            y: y - 30,
            alpha: 0,
            duration: 1000,
            ease: 'Power2',
            onComplete: () => ft.destroy()
        });
    }

    checkLevelUp() {
        while (this.state.xp >= this.state.xpToNext) {
            this.state.xp -= this.state.xpToNext;
            this.state.level++;
            this.state.maxWill += 10;
            this.state.will = Math.min(this.state.will + 20, this.state.maxWill);
            this.state.xpToNext = Math.floor(this.state.xpToNext * 1.5);
            this.state.maxInsight += 2;
            this.state.insight = this.state.maxInsight;

            this.showFloatingText(this.seeker.x, this.seeker.y - 30, `LEVEL ${this.state.level}!`, '#ffdd00');

            // Flash effect
            this.cameras.main.flash(500, 240, 192, 64, true);
        }
    }

    update(time, delta) {
        if (!this.seeker || !this.seeker.active) return;

        // --- Player movement ---
        const speed = 120;
        let vx = 0, vy = 0;

        if (this.cursors.left.isDown || this.wasd.A.isDown) vx = -1;
        if (this.cursors.right.isDown || this.wasd.D.isDown) vx = 1;
        if (this.cursors.up.isDown || this.wasd.W.isDown) vy = -1;
        if (this.cursors.down.isDown || this.wasd.S.isDown) vy = 1;

        // Normalize diagonal
        if (vx !== 0 && vy !== 0) {
            vx *= 0.707;
            vy *= 0.707;
        }

        this.seeker.setVelocity(vx * speed, vy * speed);

        // Animation
        if (vx !== 0 || vy !== 0) {
            this.seeker.playWalkAnimation(vx, vy);
        } else {
            this.seeker.playIdle();
        }

        // --- Skill cooldowns ---
        for (const skill of ['measure', 'compress', 'transmute', 'break']) {
            if (this.state.skills[skill].cd > 0) {
                this.state.skills[skill].cd = Math.max(0, this.state.skills[skill].cd - delta);
            }
        }

        // --- Skill usage ---
        if (Phaser.Input.Keyboard.JustDown(this.key1)) {
            this.combat.useSkill(this.seeker, 'measure', this.state);
        }
        if (Phaser.Input.Keyboard.JustDown(this.key2)) {
            this.combat.useSkill(this.seeker, 'compress', this.state);
        }
        if (Phaser.Input.Keyboard.JustDown(this.key3)) {
            this.combat.useSkill(this.seeker, 'transmute', this.state);
        }
        if (Phaser.Input.Keyboard.JustDown(this.key4)) {
            this.combat.useSkill(this.seeker, 'break', this.state);
        }

        // --- Interaction ---
        if (Phaser.Input.Keyboard.JustDown(this.keyE)) {
            this.interact();
        }

        // --- Basic attack on space ---
        if (Phaser.Input.Keyboard.JustDown(this.keySpace)) {
            // Attack in facing direction
            const pointer = this.input.activePointer;
            this.combat.basicAttack(this.seeker, pointer);
        }

        // --- Enemy AI ---
        this.enemies.getChildren().forEach(enemy => {
            if (enemy.active && enemy.ai) {
                enemy.ai.update(time, delta, this.seeker);
            }
        });

        // --- Update projectiles ---
        this.projectiles.getChildren().forEach(p => {
            if (p.active && p.lifespan) {
                p.lifespan -= delta;
                if (p.lifespan <= 0) p.destroy();
            }
        });
        this.enemyProjectiles.getChildren().forEach(p => {
            if (p.active && p.lifespan) {
                p.lifespan -= delta;
                if (p.lifespan <= 0) p.destroy();
            }
        });

        // --- Check room cleared ---
        if (this.state.enemiesRemaining <= 0 && !this.state.roomCleared) {
            this.state.roomCleared = true;
            this.showCompanionLine(Phaser.Math.Between(0, this.state.companionLines.length - 1));
        }

        // --- Update darkness (light around seeker) ---
        this.updateDarkness();

        // --- Emit state to UI ---
        this.events.emit('stateUpdate', this.state);
    }

    updateDarkness() {
        const darkness = this.darkness;
        darkness.clear();

        // Full dark overlay
        darkness.fillStyle(0x000000, 0.6);
        darkness.fillRect(0, 0, this.worldWidth, this.worldHeight);

        // Cut out light around seeker
        const sx = this.seeker.x;
        const sy = this.seeker.y;
        const lightRadius = 80 + this.state.light * 10;

        darkness.fillStyle(0x000000, 0);
        darkness.fillCircle(sx, sy, lightRadius);
        // Multiple cuts for soft edge
        darkness.fillStyle(0x000000, 0.15);
        darkness.fillCircle(sx, sy, lightRadius + 20);
        darkness.fillStyle(0x000000, 0.1);
        darkness.fillCircle(sx, sy, lightRadius + 40);
    }

    interact() {
        const seeker = this.seeker;
        const interactDist = 40;

        // Check shrines
        for (const shrine of this.shrineTiles) {
            const dist = Phaser.Math.Distance.Between(seeker.x, seeker.y, shrine.x, shrine.y);
            if (dist < interactDist) {
                if (!shrine.used) {
                    shrine.used = true;
                    this.state.will = Math.min(this.state.maxWill, this.state.will + 30);
                    this.state.xp += 5;
                    this.showFloatingText(shrine.x, shrine.y - 20, 'SHRINE RESTORED +30 WILL', '#f0c040');
                    this.showCompanionLine(Phaser.Math.Between(0, this.state.companionLines.length - 1));

                    // Glow effect
                    const glow = this.add.circle(shrine.x, shrine.y, 20, 0xf0c040, 0.3).setDepth(4);
                    this.tweens.add({
                        targets: glow,
                        alpha: 0,
                        scale: 2,
                        duration: 1000,
                        onComplete: () => glow.destroy()
                    });
                }
                return;
            }
        }

        // Check stairs
        for (const stairs of this.stairTiles) {
            const dist = Phaser.Math.Distance.Between(seeker.x, seeker.y, stairs.x, stairs.y);
            if (dist < interactDist) {
                if (this.state.enemiesRemaining <= 0) {
                    this.descendFloor();
                } else {
                    this.showFloatingText(seeker.x, seeker.y - 20, 'DEFEAT ALL ENEMIES FIRST', '#ff4444');
                }
                return;
            }
        }
    }

    descendFloor() {
        if (this.floor >= this.maxFloor) {
            // Victory!
            this.showFloatingText(this.seeker.x, this.seeker.y - 40, 'THE LONG LIGHT ACHIEVED', '#ffdd00');
            this.cameras.main.flash(1000, 240, 192, 64);
            this.time.delayedCall(2000, () => {
                this.scene.stop('UIScene');
                this.scene.restart({ floor: 1, seekerData: null });
            });
            return;
        }

        // Save state and descend
        const seekerData = { ...this.state };
        this.scene.stop('UIScene');
        this.scene.restart({
            floor: this.floor + 1,
            seekerData: seekerData
        });
    }

    onEnemyDefeated(enemy) {
        this.state.enemiesRemaining--;

        // Drop loot
        this.loot.dropLoot(enemy.x, enemy.y, this.state);

        // XP
        const xpGain = enemy.boss ? 30 : 10;
        this.state.xp += xpGain;
        this.showFloatingText(enemy.x, enemy.y - 20, `+${xpGain} XP`, '#f0c040');
        this.checkLevelUp();

        // Screen shake on boss defeat
        if (enemy.boss) {
            this.cameras.main.shake(300, 0.01);
            this.showCompanionLine(Phaser.Math.Between(0, this.state.companionLines.length - 1));
        }

        this.events.emit('stateUpdate', this.state);
    }
}
