/**
 * SEEKER — Player entity
 * Top-down movement, animation, stats
 */
export class Seeker extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y) {
        super(scene, x, y, 'seeker');

        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.setCollideWorldBounds(true);
        this.body.setSize(16, 20);
        this.body.setOffset(8, 24);

        // Facing direction
        this.facingX = 0;
        this.facingY = 1;

        // Animation state
        this.walkFrame = 0;
        this.walkTimer = 0;
    }

    playWalkAnimation(vx, vy) {
        if (vx !== 0 || vy !== 0) {
            this.facingX = vx;
            this.facingY = vy;
        }

        // Flip based on direction
        this.setFlipX(vx < 0);

        // Simple frame cycling
        this.walkTimer += 1;
        if (this.walkTimer > 8) {
            this.walkTimer = 0;
            this.walkFrame = (this.walkFrame + 1) % 4;
            this.setTexture(`seeker_walk_${this.walkFrame}`);
        }
    }

    playIdle() {
        this.setTexture('seeker');
        this.walkFrame = 0;
        this.walkTimer = 0;
    }
}
