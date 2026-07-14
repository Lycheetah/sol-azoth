/**
 * THE LONG LIGHT — School Dungeon
 * Main game entry point — Phaser 3
 * Lycheetah Mystery School · Diablo top-down
 *
 * A visual masterpiece: procedurally-generated pixel art,
 * LAMAGUE symbolic combat, dark parchment void aesthetic.
 */

import { BootScene } from './scenes/BootScene.js';
import { GameScene } from './scenes/GameScene.js';
import { UIScene } from './scenes/UIScene.js';

const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'game',
    pixelArt: true,
    backgroundColor: '#0a0808',
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    scene: [BootScene, GameScene, UIScene],
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    render: {
        antialias: false,
        pixelArt: true,
        roundPixels: true
    }
};

const game = new Phaser.Game(config);
