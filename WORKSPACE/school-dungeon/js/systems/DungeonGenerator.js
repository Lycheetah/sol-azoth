/**
 * DUNGEON GENERATOR — Procedural room-based dungeon
 * Generates interconnected rooms with corridors
 * Tile types: 0=void, 1=wall, 2=floor, 3=door, 4=shrine, 5=stairs
 */
export class DungeonGenerator {
    constructor(scene) {
        this.scene = scene;
    }

    generate(floor) {
        const mapWidth = 50;
        const mapHeight = 38;
        const map = [];

        // Initialize with walls
        for (let y = 0; y < mapHeight; y++) {
            map[y] = [];
            for (let x = 0; x < mapWidth; x++) {
                map[y][x] = 1; // wall
            }
        }

        // Generate rooms using BSP-like placement
        const rooms = this.generateRooms(map, mapWidth, mapHeight, floor);

        // Connect rooms with corridors
        this.connectRooms(map, rooms);

        // Place special tiles
        this.placeSpecials(map, rooms, floor);

        // Find player start (center of first room)
        const startRoom = rooms[0];
        const playerStart = {
            x: Math.floor(startRoom.x + startRoom.w / 2),
            y: Math.floor(startRoom.y + startRoom.h / 2)
        };

        return { map, rooms, playerStart };
    }

    generateRooms(map, mapWidth, mapHeight, floor) {
        const rooms = [];
        const minSize = 5;
        const maxSize = 9;
        const maxAttempts = 30;

        // First room (guaranteed)
        const firstRoom = {
            id: 0,
            x: 2, y: 2,
            w: 7, h: 6
        };
        this.carveRoom(map, firstRoom);
        rooms.push(firstRoom);

        // Additional rooms
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            const w = Phaser.Math.Between(minSize, maxSize);
            const h = Phaser.Math.Between(minSize, maxSize);
            const x = Phaser.Math.Between(1, mapWidth - w - 1);
            const y = Phaser.Math.Between(1, mapHeight - h - 1);

            const room = { id: rooms.length, x, y, w, h };

            if (this.isRoomValid(map, room, rooms)) {
                this.carveRoom(map, room);
                rooms.push(room);
            }
        }

        return rooms;
    }

    isRoomValid(map, room, existingRooms) {
        // Check bounds
        if (room.x + room.w >= map[0].length - 1 || room.y + room.h >= map.length - 1) {
            return false;
        }

        // Check overlap with existing rooms (with 2-tile padding)
        for (const other of existingRooms) {
            if (
                room.x - 2 < other.x + other.w &&
                room.x + room.w + 2 > other.x &&
                room.y - 2 < other.y + other.h &&
                room.y + room.h + 2 > other.y
            ) {
                return false;
            }
        }

        return true;
    }

    carveRoom(map, room) {
        for (let y = room.y; y < room.y + room.h; y++) {
            for (let x = room.x; x < room.x + room.w; x++) {
                map[y][x] = 2; // floor
            }
        }
    }

    connectRooms(map, rooms) {
        for (let i = 1; i < rooms.length; i++) {
            // Connect to previous room
            const prev = rooms[i - 1];
            const curr = rooms[i];

            const prevCenter = {
                x: Math.floor(prev.x + prev.w / 2),
                y: Math.floor(prev.y + prev.h / 2)
            };
            const currCenter = {
                x: Math.floor(curr.x + curr.w / 2),
                y: Math.floor(curr.y + curr.h / 2)
            };

            // L-shaped corridor
            if (Math.random() > 0.5) {
                this.carveHCorridor(map, prevCenter.x, currCenter.x, prevCenter.y);
                this.carveVCorridor(map, prevCenter.y, currCenter.y, currCenter.x);
            } else {
                this.carveVCorridor(map, prevCenter.y, currCenter.y, prevCenter.x);
                this.carveHCorridor(map, prevCenter.x, currCenter.x, currCenter.y);
            }

            // Place doors at room entrances
            this.placeDoor(map, curr.x, curr.y, curr.w, curr.h);
        }
    }

    carveHCorridor(map, x1, x2, y) {
        const start = Math.min(x1, x2);
        const end = Math.max(x1, x2);
        for (let x = start; x <= end; x++) {
            if (y >= 0 && y < map.length && x >= 0 && x < map[0].length) {
                map[y][x] = 2;
                // Also clear above/below for wider corridor
                if (y + 1 < map.length) map[y + 1][x] = 2;
            }
        }
    }

    carveVCorridor(map, y1, y2, x) {
        const start = Math.min(y1, y2);
        const end = Math.max(y1, y2);
        for (let y = start; y <= end; y++) {
            if (y >= 0 && y < map.length && x >= 0 && x < map[0].length) {
                map[y][x] = 2;
                if (x + 1 < map[0].length) map[y][x + 1] = 2;
            }
        }
    }

    placeDoor(map, rx, ry, rw, rh) {
        // Place door at room entrance (center of first wall)
        const cx = Math.floor(rx + rw / 2);
        const cy = Math.floor(ry + rh / 2);

        // Check all four sides for corridor connection
        const sides = [
            { x: cx, y: ry - 1, dx: 0, dy: -1 },
            { x: cx, y: ry + rh, dx: 0, dy: 1 },
            { x: rx - 1, y: cy, dx: -1, dy: 0 },
            { x: rx + rw, y: cy, dx: 1, dy: 0 }
        ];

        for (const side of sides) {
            const checkY = side.y + side.dy;
            const checkX = side.x + side.dx;
            if (
                checkY >= 0 && checkY < map.length &&
                checkX >= 0 && checkX < map[0].length &&
                map[checkY][checkX] === 2
            ) {
                if (side.y >= 0 && side.y < map.length &&
                    side.x >= 0 && side.x < map[0].length) {
                    map[side.y][side.x] = 3; // door
                }
                return;
            }
        }
    }

    placeSpecials(map, rooms, floor) {
        // Place shrine in room 1 (if exists)
        if (rooms.length > 1) {
            const shrineRoom = rooms[1];
            const sx = Math.floor(shrineRoom.x + shrineRoom.w / 2);
            const sy = Math.floor(shrineRoom.y + shrineRoom.h / 2);
            map[sy][sx] = 4; // shrine
        }

        // Place stairs in last room
        if (rooms.length > 2) {
            const lastRoom = rooms[rooms.length - 1];
            const stx = Math.floor(lastRoom.x + lastRoom.w / 2);
            const sty = Math.floor(lastRoom.y + lastRoom.h / 2);
            map[sty][stx] = 5; // stairs
        } else {
            // Fallback: stairs in first room
            const firstRoom = rooms[0];
            const stx = Math.floor(firstRoom.x + firstRoom.w / 2);
            const sty = Math.floor(firstRoom.y + firstRoom.h / 2);
            map[sty + 2][stx] = 5;
        }
    }
}
