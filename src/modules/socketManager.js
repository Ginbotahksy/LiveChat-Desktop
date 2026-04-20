const { io } = require("socket.io-client");
const configManager = require("./configManager");

class SocketManager {
    constructor() {
        this.socket = null;
        this.win = null;
        this.botClientId = null;
        this.clientGuilds = [];
        this.onGuildsUpdate = null; // Callback pour mettre à jour le Tray
    }

    init(win, onGuildsUpdate) {
        this.win = win;
        this.onGuildsUpdate = onGuildsUpdate;

        const socketUrl = process.env.SOCKET_URL || "http://iceboxer.hd.free.fr:8080";
        this.socket = io(socketUrl);

        this.socket.on("connect", () => {
            console.log("Connecté au serveur Socket");
            if (configManager.userId) {
                this.getMyGuilds();
            }
        });

        this.socket.on("bot-config", (config) => {
            console.log("Config reçue du bot :", config);
            this.botClientId = config.clientId;
            if (this.onGuildsUpdate) this.onGuildsUpdate();
        });

        this.socket.on("list-guilds", (guilds) => {
            console.log(`Liste des serveurs reçue (${guilds.length} serveurs)`);
            this.clientGuilds = guilds;
            
            // On rejoint les rooms actives
            configManager.activeRooms.forEach(roomId => {
                if (guilds.some(g => g.id === roomId)) {
                    console.log(`Rejoint la room active : ${roomId}`);
                    this.joinRoom(roomId);
                } else {
                    configManager.activeRooms.delete(roomId);
                }
            });

            configManager.saveConfig();
            if (this.onGuildsUpdate) this.onGuildsUpdate();
        });

        this.socket.on("display-media", (data) => {
            if (this.win) {
                this.win.webContents.send('set-class', data.format);
                this.win.webContents.send('update-media', data);
            }
        });

        this.socket.on("stop", () => {
            if (this.win) this.win.webContents.send('stop');
        });
    }

    getMyGuilds() {
        if (this.socket && configManager.userId) {
            this.socket.emit("get-my-guilds", configManager.userId);
        }
    }

    joinRoom(guildId) {
        if (this.socket) this.socket.emit("join-server-room", guildId);
    }

    leaveRoom(guildId) {
        if (this.socket) this.socket.emit("leave-server-room", guildId);
    }
}

module.exports = new SocketManager();
