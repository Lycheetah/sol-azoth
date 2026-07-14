/**
 * LOOT SYSTEM — Enemy drops and item spawning
 */
export class LootSystem {
    constructor(scene) {
        this.scene = scene;
    }

    /**
     * Drop loot at enemy death position
     */
    dropLoot(x, y, state) {
        const roll = Math.random();

        // Always drop something useful
        if (roll < 0.4) {
            this.spawnItem(x, y, 'glyph_shard');
        } else if (roll < 0.7) {
            this.spawnItem(x, y, 'health_vial');
        } else if (roll < 0.85) {
            this.spawnItem(x, y, 'light_essence');
        } else {
            // Double drop!
            this.spawnItem(x, y, 'glyph_shard');
            this.spawnItem(x, y + 16, 'health_vial');
        }

        // XP essence particles
        for (let i = 0; i < 3; i++) {
            const px = x + Phaser.Math.Between(-8, 8);
            const py = y + Phaser.Math.Between(-8, 8);
            const particle = this.scene.add.circle(px, py, 2, 0xf0c040, 0.5).setDepth(8);

            this.scene.tweens.add({
                targets: particle,
                x: px + Phaser.Math.Between(-15, 15),
                y: py - Phaser.Math.Between(10, 25),
                alpha: 0,
                duration: 600,
                delay: i * 100,
                onComplete: () => particle.destroy()
            });
        }
    }

    /**
     * Spawn a pickup item with animation
     */
    spawnItem(x, y, type) {
        const item = this.scene.physics.add.sprite(x, y, type);
        item.setDepth(2);
        item.itemType = type;
        this.scene.items.add(item);

        // Pop-in animation
        item.setScale(0);
        this.scene.tweens.add({
            targets: item,
            scale: 1,
            duration: 300,
            ease: 'Back.easeOut'
        });

        // Floating animation
        this.scene.tweens.add({
            targets: item,
            y: y - 4,
            duration: 1500,
            yoyo: true,
            repeat: -1,
            ease: 'Sine.easeInOut'
        });

        // Glow pulse
        this.scene.tweens.add({
            targets: item,
            alpha: { from: 1, to: 0.7 },
            duration: 800,
            yoyo: true,
            repeat: -1
        });
    }
}
