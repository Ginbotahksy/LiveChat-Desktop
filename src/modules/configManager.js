const fs = require('node:fs');
const path = require('node:path');
const { app } = require('electron');

const CONFIG_PATH = path.join(app.getPath('userData'), 'configLiveChat.json');

class ConfigManager {
    constructor() {
        this.userId = null;
        this.activeRooms = new Set();
    }

    loadConfig() {
        if (fs.existsSync(CONFIG_PATH)) {
            try {
                const data = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
                this.userId = data.userId || null;
                this.activeRooms = new Set(data.activeRooms || []);
                console.log("Configuration chargée depuis :", CONFIG_PATH);
                return true;
            } catch (error) {
                console.error("Erreur lors du chargement de la config :", error);
            }
        }
        return false;
    }

    saveConfig() {
        try {
            const config = {
                userId: this.userId,
                activeRooms: Array.from(this.activeRooms)
            };
            fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
            console.log("Configuration enregistrée à :", CONFIG_PATH);
        } catch (error) {
            console.error("Erreur lors de la sauvegarde de la config :", error);
        }
    }

    setUserId(id) {
        console.log("Configuration de l'ID utilisateur :", id);
        this.userId = id;
        this.saveConfig();
    }

    logout() {
        console.log("Déconnexion de l'utilisateur...");
        this.userId = null;
        this.activeRooms.clear();
        this.saveConfig();
    }

    toggleRoom(guildId) {
        if (this.activeRooms.has(guildId)) {
            this.activeRooms.delete(guildId);
        } else {
            this.activeRooms.add(guildId);
        }
        this.saveConfig();
        return this.activeRooms.has(guildId);
    }
}

module.exports = new ConfigManager();
