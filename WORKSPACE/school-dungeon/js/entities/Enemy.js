/**
 * ENEMY — Dungeon enemies with AI
 * Each enemy has a type, stats, and behavior
 */
export class Enemy extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y, type, boss = false) {
        const textureKey = Enemy.getTextureForType(type);
        super(scene, x, y, textureKey);

        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.setCollideWorldBounds(true);
        this.body.setSize(24, 24);
        this.body.setOffset(4, 4);

        // Properties
        this.enemyType = type;
        this.boss = boss;
        this.stats = Enemy.getStatsForType(type, boss);
        this.currentHp = this.stats.hp;
        this.ai = new EnemyAI(scene, this);
        this.invulnerable = false;
        this.invulnTimer = 0;

        // Boss scaling
        if (boss) {
            this.setScale(1.5);
            this.body.setSize(24, 24);
            this.body.setOffset(4, 4);

            // Boss glow
            this.bossGlow = scene.add.circle(x, y, 24, 0xf0c040, 0.1).setDepth(this.depth - 1);
            scene.tweens.add({
                targets: this.bossGlow,
                alpha: 0.2,
                scale: 1.2,
                duration: 1500,
                yoyo: true,
                repeat: -1
            });
        }

        // HP bar (above enemy)
        this.hpBarBg = scene.add.rectangle(x, y - 20, 28, 4, 0x1a1818).setDepth(15);
        this.hpBar = scene.add.rectangle(x - 13, y - 20, 26, 3, 0xff4444).setOrigin(0, 0.5).setDepth(16);

        // Floating animation
        scene.tweens.add({
            targets: this,
            y: y - 3,
            duration: 2000 + Math.random() * 1000,
            yoyo: true,
            repeat: -1,
            ease: 'Sine.easeInOut'
        });
    }

    static getTextureForType(type) {
        const textures = {
            'overclaimer': 'overclaimer',
            'halfmade': 'halfmade',
            'loop': 'loop',
            'shade': 'shade'
        };
        return textures[type] || 'shade';
    }

    static getStatsForType(type, boss) {
        const base = {
            'shade': { hp: 20, damage: 5, speed: 60, xp: 5 },
            'overclaimer': { hp: 40, damage: 8, speed: 40, xp: 10 },
            'halfmade': { hp: 30, damage: 6, speed: 50, xp: 8 },
            'loop': { hp: 25, damage: 10, speed: 70, xp: 8 }
        };

        const stats = { ...base[type] || base.shade };
        if (boss) {
            stats.hp *= 3;
            stats.damage *= 2;
            stats.xp *= 3;
        }
        return stats;
    }

    takeDamage(amount) {
        if (this.invulnerable) return false;

        this.currentHp -= amount;

        // Flash white
        this.setTint(0xffffff);
        this.invulnerable = true;
        this.invulnTimer = 150;

        // Update HP bar
        const hpPct = Math.max(0, this.currentHp / this.stats.hp);
        this.hpBar.width = 26 * hpPct;

        // Knockback visual
        this.scene.tweens.add({
            targets: this,
            x: this.x + (this.x - this.scene.seeker.x) * 0.2,
            duration: 100,
            yoyo: true,
            ease: 'Power1'
        });

        if (this.currentHp <= 0) {
            this.die();
            return true;
        }
        return false;
    }

    die() {
        // Death effect
        for (let i = 0; i < 8; i++) {
            const px = this.x + Phaser.Math.Between(-10, 10);
            const py = this.y + Phaser.Math.Between(-10, 10);
            const particle = this.scene.add.circle(px, py, Phaser.Math.Between(2, 4), 0xf0c040, 0.6);
            particle.setDepth(20);

            this.scene.tweens.add({
                targets: particle,
                x: px + Phaser.Math.Between(-20, 20),
                y: py + Phaser.Math.Between(-20, 20),
                alpha: 0,
                scale: 0,
                duration: 500,
                onComplete: () => particle.destroy()
            });
        }

        if (this.bossGlow) this.bossGlow.destroy();
        this.hpBarBg.destroy();
        this.hpBar.destroy();
        this.scene.onEnemyDefeated(this);
        this.destroy();
    }

    update(time, delta) {
        if (this.invulnerable) {
            this.invulnTimer -= delta;
            if (this.invulnTimer <= 0) {
                this.invulnerable = false;
                this.clearTint();
            }
        }

        // Update HP bar position
        this.hpBarBg.setPosition(this.x, this.y - 20);
        this.hpBar.setPosition(this.x - 13, this.y - 20);

        if (this.bossGlow) {
            this.bossGlow.setPosition(this.x, this.y);
        }
    }
}

/**
 * ENEMY AI — Simple behavior patterns per type
 */
class EnemyAI {
    constructor(scene, enemy) {
        this.scene = scene;
        this.enemy = enemy;
        this.state = 'idle';
        this.stateTimer = 0;
        this.attackCooldown = 0;
        this.wanderTarget = null;
    }

    update(time, delta, seeker) {
        if (!this.enemy.active || !seeker.active) return;

        const dist = Phaser.Math.Distance.Between(this.enemy.x, this.enemy.y, seeker.x, seeker.y);
        const type = this.enemy.enemyType;

        this.stateTimer -= delta;
        this.attackCooldown = Math.max(0, this.attackCooldown - delta);

        switch (type) {
            case 'shade':
                this.behaviorShade(delta, seeker, dist);
                break;
            case 'overclaimer':
                this.behaviorOverclaimer(delta, seeker, dist);
                break;
            case 'halfmade':
                this.behaviorHalfmade(delta, seeker, dist);
                break;
            case 'loop':
                this.behaviorLoop(delta, seeker, dist);
                break;
        }
    }

    moveToward(target, speed) {
        const angle = Phaser.Math.Angle.Between(this.enemy.x, this.enemy.y, target.x, target.y);
        this.enemy.setVelocity(
            Math.cos(angle) * speed,
            Math.sin(angle) * speed
        );
    }

    moveAway(target, speed) {
        const angle = Phaser.Math.Angle.Between(target.x, target.y, this.enemy.x, this.enemy.y);
        this.enemy.setVelocity(
            Math.cos(angle) * speed,
            Math.sin(angle) * speed
        );
    }

    shootAt(target) {
        if (this.attackCooldown > 0) return;
        this.attackCooldown = 1500;

        const angle = Phaser.Math.Angle.Between(this.enemy.x, this.enemy.y, target.x, target.y);
        const bolt = this.scene.physics.add.sprite(this.enemy.x, this.enemy.y, 'enemy_bolt');
        bolt.setDepth(8);
        bolt.setVelocity(Math.cos(angle) * 150, Math.sin(angle) * 150);
        bolt.lifespan = 3000;
        this.scene.enemyProjectiles.add(bolt);
    }

    // Shade: rushes directly at player
    behaviorShade(delta, seeker, dist) {
        if (dist < 200) {
            this.moveToward(seeker, this.enemy.stats.speed * 1.2);
            if (dist < 30 && this.attackCooldown <= 0) {
                this.attackCooldown = 1000;
                this.scene.combat.enemyMeleeAttack(this.enemy, seeker);
            }
        } else {
            this.enemy.setVelocity(0, 0);
        }
    }

    // Overclaimer: keeps distance, shoots
    behaviorOverclaimer(delta, seeker, dist) {
        if (dist < 100) {
            this.moveAway(seeker, this.enemy.stats.speed * 0.8);
        } else if (dist < 250) {
            this.enemy.setVelocity(0, 0);
            this.shootAt(seeker);
        } else {
            this.moveToward(seeker, this.enemy.stats.speed * 0.6);
        }
    }

    // Halfmade: erratic movement, occasional charges
    behaviorHalfmade(delta, seeker, dist) {
        if (this.stateTimer <= 0) {
            this.state = Phaser.Math.RND.pick(['wander', 'charge', 'retreat']);
            this.stateTimer = Phaser.Math.Between(1000, 3000);
        }

        switch (this.state) {
            case 'charge':
                if (dist < 300) {
                    this.moveToward(seeker, this.enemy.stats.speed * 1.5);
                    if (dist < 30 && this.attackCooldown <= 0) {
                        this.attackCooldown = 800;
                        this.scene.combat.enemyMeleeAttack(this.enemy, seeker);
                    }
                }
                break;
            case 'retreat':
                if (dist < 200) this.moveAway(seeker, this.enemy.stats.speed);
                else this.enemy.setVelocity(0, 0);
                break;
            default:
                this.enemy.setVelocity(
                    Phaser.Math.Between(-1, 1) * this.enemy.stats.speed * 0.5,
                    Phaser.Math.Between(-1, 1) * this.enemy.stats.speed * 0.5
                );
        }
    }

    // Loop: fast, shoots, tries to circle
    behaviorLoop(delta, seeker, dist) {
        if (dist < 250) {
            // Circle around player
            const angle = Phaser.Math.Angle.Between(this.enemy.x, this.enemy.y, seeker.x, seeker.y);
            const circleAngle = angle + Math.PI / 2;
            this.enemy.setVelocity(
                Math.cos(circleAngle) * this.enemy.stats.speed,
                Math.sin(circleAngle) * this.enemy.stats.speed
            );
            this.shootAt(seeker);
        } else {
            this.moveToward(seeker, this.enemy.stats.speed);
        }
    }
}
