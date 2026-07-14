/**
 * COMBAT SYSTEM — LAMAGUE-themed combat
 * Basic attack + 4 glyph skills (MEASURE, COMPRESS, TRANSMUTE, BREAK)
 */
export class CombatSystem {
    constructor(scene) {
        this.scene = scene;
    }

    /**
     * Basic attack — fires an Insight ray toward pointer
     */
    basicAttack(seeker, pointer) {
        const worldPoint = this.scene.cameras.main.getWorldPoint(pointer.x, pointer.y);
        const angle = Phaser.Math.Angle.Between(seeker.x, seeker.y, worldPoint.x, worldPoint.y);

        const ray = this.scene.physics.add.sprite(seeker.x, seeker.y, 'insight_ray');
        ray.setDepth(8);
        ray.setRotation(angle);
        ray.setVelocity(
            Math.cos(angle) * 250,
            Math.sin(angle) * 250
        );
        ray.damage = 8 + this.scene.state.level * 2;
        ray.lifespan = 1500;

        this.scene.projectiles.add(ray);

        // Muzzle flash
        const flash = this.scene.add.circle(seeker.x, seeker.y, 6, 0xf0c040, 0.6).setDepth(9);
        this.scene.tweens.add({
            targets: flash,
            alpha: 0,
            scale: 2,
            duration: 150,
            onComplete: () => flash.destroy()
        });
    }

    /**
     * Use a LAMAGUE skill
     */
    useSkill(seeker, skillName, state) {
        const skill = state.skills[skillName];
        if (skill.cd > 0) return; // on cooldown

        const pointer = this.scene.input.activePointer;
        const worldPoint = this.scene.cameras.main.getWorldPoint(pointer.x, pointer.y);
        const angle = Phaser.Math.Angle.Between(seeker.x, seeker.y, worldPoint.x, worldPoint.y);

        switch (skillName) {
            case 'measure':
                this.skillMeasure(seeker, angle, state);
                break;
            case 'compress':
                this.skillCompress(seeker, angle, state);
                break;
            case 'transmute':
                this.skillTransmute(seeker, state);
                break;
            case 'break':
                this.skillBreak(seeker, angle, state);
                break;
        }

        // Set cooldown
        skill.cd = skill.maxCd;
    }

    /**
     * MEASURE (Π) — reveals enemy true HP, strips overclaim shields
     * Fires a cyan glyph that marks enemies, doubling damage for 3s
     */
    skillMeasure(seeker, angle, state) {
        const glyph = this.scene.physics.add.sprite(seeker.x, seeker.y, 'measure_glyph');
        glyph.setDepth(8);
        glyph.setVelocity(Math.cos(angle) * 200, Math.sin(angle) * 200);
        glyph.lifespan = 2000;
        glyph.skillType = 'measure';
        glyph.duration = 3000;

        this.scene.projectiles.add(glyph);

        // Visual
        this.scene.tweens.add({
            targets: glyph,
            scale: { from: 0.5, to: 1.5 },
            duration: 300,
            yoyo: true,
            repeat: 3
        });

        this.scene.events.emit('log', 'MEASURE — revealing truth');
    }

    /**
     * COMPRESS (⟁) — pulls enemy inward, bursts if measured
     * Fires an orange glyph that pulls enemies toward it
     */
    skillCompress(seeker, angle, state) {
        const glyph = this.scene.physics.add.sprite(seeker.x, seeker.y, 'compress_glyph');
        glyph.setDepth(8);
        glyph.setVelocity(Math.cos(angle) * 180, Math.sin(angle) * 180);
        glyph.lifespan = 1500;
        glyph.skillType = 'compress';

        this.scene.projectiles.add(glyph);

        this.scene.events.emit('log', 'COMPRESS — pulling essence inward');
    }

    /**
     * TRANSMUTE (Ω) — converts recent damage into healing
     * Heals based on missing HP
     */
    skillTransmute(seeker, state) {
        const missingHp = state.maxWill - state.will;
        const healAmount = Math.floor(missingHp * 0.4) + 10;

        state.will = Math.min(state.maxWill, state.will + healAmount);

        // Green burst around seeker
        for (let i = 0; i < 12; i++) {
            const angle = (i / 12) * Math.PI * 2;
            const px = seeker.x + Math.cos(angle) * 20;
            const py = seeker.y + Math.sin(angle) * 20;
            const particle = this.scene.add.circle(px, py, 3, 0x00ff88, 0.6).setDepth(9);

            this.scene.tweens.add({
                targets: particle,
                x: px + Math.cos(angle) * 30,
                y: py + Math.sin(angle) * 30,
                alpha: 0,
                scale: 0,
                duration: 500,
                onComplete: () => particle.destroy()
            });
        }

        this.scene.showFloatingText(seeker.x, seeker.y - 30, `+${healAmount} WILL`, '#00ff88');
        this.scene.events.emit('log', `TRANSMUTE — converted ${healAmount} will from shadow`);
    }

    /**
     * BREAK (⫸) — interrupts enemy attacks, stuns
     * Fires a violet glyph that stuns on hit
     */
    skillBreak(seeker, angle, state) {
        const glyph = this.scene.physics.add.sprite(seeker.x, seeker.y, 'break_glyph');
        glyph.setDepth(8);
        glyph.setVelocity(Math.cos(angle) * 220, Math.sin(angle) * 220);
        glyph.lifespan = 1000;
        glyph.skillType = 'break';

        this.scene.projectiles.add(glyph);

        // Screen jolt
        this.scene.cameras.main.shake(100, 0.003);

        this.scene.events.emit('log', 'BREAK — interrupting the pattern');
    }

    /**
     * Called when a projectile hits an enemy
     */
    onProjectileHitEnemy(projectile, enemy) {
        if (!projectile.active || !enemy.active) return;

        let damage = 0;
        let isMeasure = false;

        switch (projectile.skillType) {
            case 'measure':
                damage = 5;
                isMeasure = true;
                // Mark enemy for double damage
                enemy.setTint(0x00ccff);
                enemy.measured = true;
                this.scene.time.delayedCall(3000, () => {
                    if (enemy.active) {
                        enemy.measured = false;
                        enemy.clearTint();
                    }
                });
                this.scene.showFloatingText(enemy.x, enemy.y - 20, 'MEASURED', '#00ccff');
                break;

            case 'compress':
                damage = 15;
                if (enemy.measured) {
                    damage *= 2;
                    this.scene.showFloatingText(enemy.x, enemy.y - 20, `COMPRESSED x2!`, '#ff6600');
                    enemy.measured = false;
                    enemy.clearTint();
                }
                // Pull enemy toward projectile
                this.scene.tweens.add({
                    targets: enemy,
                    x: projectile.x,
                    y: projectile.y,
                    duration: 200,
                    ease: 'Power2'
                });
                break;

            case 'break':
                damage = 10;
                // Stun: stop enemy movement briefly
                enemy.setVelocity(0, 0);
                enemy.invulnerable = true;
                enemy.setTint(0xcc44ff);
                this.scene.showFloatingText(enemy.x, enemy.y - 20, 'STUNNED', '#cc44ff');
                this.scene.time.delayedCall(1500, () => {
                    if (enemy.active) {
                        enemy.invulnerable = false;
                        enemy.clearTint();
                    }
                });
                break;

            default:
                // Basic attack
                damage = projectile.damage || 8;
                break;
        }

        if (damage > 0) {
            const killed = enemy.takeDamage(damage);
            this.scene.showFloatingText(enemy.x, enemy.y - 10, `${damage}`, '#ffffff');
        }

        projectile.destroy();
    }

    /**
     * Enemy projectile hits seeker
     */
    onEnemyProjectileHitSeeker(seeker, projectile) {
        if (!projectile.active || !seeker.active) return;

        const damage = projectile.damage || 5;
        this.seekerTakeDamage(seeker, damage);
        projectile.destroy();
    }

    /**
     * Seeker touches enemy (melee contact damage)
     */
    onSeekerTouchEnemy(seeker, enemy) {
        if (!seeker.active || !enemy.active) return;
        // Handled by enemy AI melee attacks instead
    }

    /**
     * Enemy melee attack
     */
    enemyMeleeAttack(enemy, seeker) {
        this.seekerTakeDamage(seeker, enemy.stats.damage);
    }

    /**
     * Seeker takes damage
     */
    seekerTakeDamage(seeker, damage) {
        const state = this.scene.state;
        state.will = Math.max(0, state.will - damage);

        // Red flash
        seeker.setTint(0xff4444);
        this.scene.time.delayedCall(100, () => {
            if (seeker.active) seeker.clearTint();
        });

        // Screen shake
        this.scene.cameras.main.shake(100, 0.005);

        // Floating damage
        this.scene.showFloatingText(seeker.x, seeker.y - 20, `-${damage}`, '#ff4444');

        // Death check
        if (state.will <= 0) {
            this.seekerDeath(seeker);
        }

        this.scene.events.emit('stateUpdate', state);
    }

    /**
     * Seeker death — soft respawn at last shrine
     */
    seekerDeath(seeker) {
        const state = this.scene.state;

        // Find nearest shrine or start
        let respawnX = this.scene.dungeon.playerStart.x * 32 + 16;
        let respawnY = this.scene.dungeon.playerStart.y * 32 + 16;

        for (const shrine of this.scene.shrineTiles) {
            if (shrine.used) {
                respawnX = shrine.x;
                respawnY = shrine.y;
                break;
            }
        }

        // Death animation
        this.scene.cameras.main.shake(500, 0.02);
        this.scene.cameras.main.flash(500, 255, 0, 0);

        // Respawn after delay
        this.scene.time.delayedCall(1500, () => {
            state.will = Math.floor(state.maxWill * 0.5);
            seeker.setPosition(respawnX, respawnY);
            seeker.clearTint();
            this.scene.showFloatingText(respawnX, respawnY - 20, 'RESTORED AT SHRINE', '#f0c040');
            this.scene.showCompanionLine(3); // "Rest when you need to"

            // Half enemies respawn
            this.scene.enemies.getChildren().forEach(enemy => {
                if (!enemy.active) {
                    // Don't respawn — keep progress
                }
            });

            this.scene.events.emit('stateUpdate', state);
        });
    }
}
