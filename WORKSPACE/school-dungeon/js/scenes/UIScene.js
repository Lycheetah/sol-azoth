/**
 * UI SCENE — Overlay HUD
 * Rendered on top of the game world — HP, XP, skills, companion, log
 */
export class UIScene extends Phaser.Scene {
    constructor() {
        super({ key: 'UIScene' });
    }

    init(data) {
        this.floor = data.floor || 1;
        this.maxFloor = data.maxFloor || 4;
        this.state = data.state || null;
    }

    create() {
        const w = this.cameras.main.width;
        const h = this.cameras.main.height;

        // --- HP Bar (top-left) ---
        this.hpBarBg = this.add.rectangle(20, 20, 200, 16, 0x1a1818).setOrigin(0, 0);
        this.hpBarBg.setStrokeStyle(1, 0xf0c040, 0.4);
        this.hpBar = this.add.rectangle(21, 21, 198, 14, 0x00ff88).setOrigin(0, 0);
        this.hpLabel = this.add.text(22, 21, '', {
            fontFamily: 'monospace',
            fontSize: '10px',
            color: '#ffffff'
        });

        // --- XP Bar (below HP) ---
        this.xpBarBg = this.add.rectangle(20, 40, 200, 8, 0x1a1818).setOrigin(0, 0);
        this.xpBarBg.setStrokeStyle(1, 0xf0c040, 0.3);
        this.xpBar = this.add.rectangle(21, 41, 0, 6, 0xf0c040).setOrigin(0, 0);
        this.xpLabel = this.add.text(22, 41, '', {
            fontFamily: 'monospace',
            fontSize: '8px',
            color: '#f0c040'
        });

        // --- Floor indicator (top-right) ---
        this.floorText = this.add.text(w - 20, 20, '', {
            fontFamily: 'monospace',
            fontSize: '14px',
            color: '#f0c040',
            align: 'right'
        }).setOrigin(1, 0);

        const stageNames = ['NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO'];
        this.stageText = this.add.text(w - 20, 36, stageNames[this.floor - 1] || '', {
            fontFamily: 'monospace',
            fontSize: '10px',
            color: '#888888',
            align: 'right'
        }).setOrigin(1, 0);

        // --- Level (top-left below XP) ---
        this.levelText = this.add.text(20, 52, '', {
            fontFamily: 'monospace',
            fontSize: '11px',
            color: '#ffdd00'
        }).setOrigin(0, 0);

        // --- Glyph shards ---
        this.glyphText = this.add.text(20, 66, '', {
            fontFamily: 'monospace',
            fontSize: '11px',
            color: '#f0c040'
        }).setOrigin(0, 0);

        // --- Light level ---
        this.lightText = this.add.text(20, 80, '', {
            fontFamily: 'monospace',
            fontSize: '11px',
            color: '#aaddff'
        }).setOrigin(0, 0);

        // --- Skill bar (bottom) ---
        this.createSkillBar(w, h);

        // --- Companion line (bottom area, above skills) ---
        this.companionText = this.add.text(w / 2, h - 80, '', {
            fontFamily: 'monospace',
            fontSize: '11px',
            color: '#f0c040',
            align: 'center',
            fontStyle: 'italic'
        }).setOrigin(0.5, 1).setAlpha(0);

        // --- Log (bottom-left, above skills) ---
        this.logText = this.add.text(20, h - 100, '', {
            fontFamily: 'monospace',
            fontSize: '10px',
            color: '#888888',
            wordWrap: { width: 300 }
        }).setOrigin(0, 0).setAlpha(0.7);

        // --- Kill counter ---
        this.killText = this.add.text(w - 20, 56, '', {
            fontFamily: 'monospace',
            fontSize: '11px',
            color: '#ff6666',
            align: 'right'
        }).setOrigin(1, 0);

        // --- Listen for state updates ---
        const gameScene = this.scene.get('GameScene');
        gameScene.events.on('stateUpdate', this.updateHUD, this);
        gameScene.events.on('companionLine', this.showCompanionLine, this);
        gameScene.events.on('log', this.addLog, this);

        // Initial update
        if (this.state) this.updateHUD(this.state);
    }

    createSkillBar(w, h) {
        const skills = ['MEASURE', 'COMPRESS', 'TRANSMUTE', 'BREAK'];
        const keys = ['1', '2', '3', '4'];
        const colors = ['#00ccff', '#ff6600', '#00ff88', '#cc44ff'];
        const startX = w / 2 - 100;
        const startY = h - 50;

        this.skillSlots = [];

        for (let i = 0; i < 4; i++) {
            const x = startX + i * 55;

            const bg = this.add.rectangle(x, startY, 48, 48, 0x1a1818, 0.9);
            bg.setStrokeStyle(1, Phaser.Display.Color.HexStringToColor(colors[i]).color, 0.5);
            bg.setOrigin(0.5);

            const keyText = this.add.text(x - 16, startY - 16, keys[i], {
                fontFamily: 'monospace',
                fontSize: '9px',
                color: '#666666'
            });

            const nameText = this.add.text(x, startY + 2, skills[i].charAt(0), {
                fontFamily: 'monospace',
                fontSize: '18px',
                color: colors[i]
            }).setOrigin(0.5);

            const cdText = this.add.text(x, startY + 16, '', {
                fontFamily: 'monospace',
                fontSize: '9px',
                color: '#ff4444'
            }).setOrigin(0.5);

            this.skillSlots.push({
                bg, keyText, nameText, cdText, color: colors[i]
            });
        }
    }

    updateHUD(state) {
        if (!state) return;

        // HP
        const hpPct = state.will / state.maxWill;
        this.hpBar.width = 198 * hpPct;
        this.hpBar.fillColor = hpPct > 0.5 ? 0x00ff88 : hpPct > 0.25 ? 0xffaa00 : 0xff4444;
        this.hpLabel.setText(`WILL ${state.will}/${state.maxWill}`);

        // XP
        const xpPct = state.xp / state.xpToNext;
        this.xpBar.width = 198 * xpPct;
        this.xpLabel.setText(`XP ${state.xp}/${state.xpToNext}`);

        // Level
        this.levelText.setText(`LV ${state.level}`);

        // Glyphs
        this.glyphText.setText(`⟐ ${state.glyphShards}`);

        // Light
        this.lightText.setText(`☀ ${state.light}`);

        // Floor
        this.floorText.setText(`FLOOR ${state.floor}/${this.maxFloor}`);

        // Enemies remaining
        this.killText.setText(`☠ ${state.enemiesRemaining}`);

        // Skill cooldowns
        const skillKeys = ['measure', 'compress', 'transmute', 'break'];
        for (let i = 0; i < 4; i++) {
            const cd = state.skills[skillKeys[i]].cd;
            const maxCd = state.skills[skillKeys[i]].maxCd;
            if (cd > 0) {
                this.skillSlots[i].cdText.setText(`${(cd / 1000).toFixed(1)}s`);
                this.skillSlots[i].bg.setStrokeStyle(1, 0x444444, 0.6);
                this.skillSlots[i].nameText.setAlpha(0.4);
            } else {
                this.skillSlots[i].cdText.setText('');
                const color = Phaser.Display.Color.HexStringToColor(this.skillSlots[i].color).color;
                this.skillSlots[i].bg.setStrokeStyle(1, color, 0.6);
                this.skillSlots[i].nameText.setAlpha(1);
            }
        }
    }

    showCompanionLine(line) {
        this.companionText.setText(line);
        this.companionText.setAlpha(1);

        // Fade out slowly
        this.tweens.killTweensOf(this.companionText);
        this.tweens.add({
            targets: this.companionText,
            alpha: 0,
            duration: 6000,
            delay: 4000,
            ease: 'Power1'
        });
    }

    addLog(msg) {
        this.logText.setText(msg);
        this.logText.setAlpha(0.7);
        this.tweens.killTweensOf(this.logText);
        this.tweens.add({
            targets: this.logText,
            alpha: 0,
            duration: 4000,
            delay: 3000
        });
    }
}
