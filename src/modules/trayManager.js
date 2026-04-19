const { Tray, Menu, nativeImage, screen, shell, app } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const configManager = require("./configManager");
const socketManager = require("./socketManager");

class TrayManager {
    constructor() {
        this.tray = null;
        this.win = null;
    }

    init(win) {
        this.win = win;

        // Utilisation de __dirname pour trouver l'icône par rapport au script, peu importe l'installation
        const iconPath = path.join(__dirname, '../../assets/icons/romain_guillon.jpg');
        console.log("Recherche de l'icône Tray à :", iconPath);
        
        let icon;
        if (fs.existsSync(iconPath)) {
            icon = nativeImage.createFromPath(iconPath).resize({ width: 32, height: 32 });
        } else {
            console.warn("Icône non trouvée à :", iconPath, ". Utilisation du fallback.");
            // Fallback icon
            icon = nativeImage.createFromDataURL('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAIKADAAQAAAABAAAAIAAAAACshmLzAAAAHElEQVRYCe3BMQEAAADCoPVPbQ0PoAAAAADgNxVrAAH4wdylAAAAAElFTkSuQmCC');
        }

        this.tray = new Tray(icon);
        this.tray.setToolTip('LiveChat-Desktop');

        this.updateMenu();

        screen.on('display-added', () => this.updateMenu());
        screen.on('display-removed', () => this.updateMenu());
    }

    updateMenu() {
        if (!this.tray) return;
        console.log("Mise à jour du menu Tray. Utilisateur :", configManager.userId, "| Serveurs :", socketManager.clientGuilds.length);

        const displays = screen.getAllDisplays();
        const displayItems = displays.map((display, index) => ({
            label: `Écran ${index + 1}: ${display.label}`,
            type: 'radio',
            checked: this.win ? this.win.getBounds().x === display.bounds.x : index === 0,
            click: () => {
                const { x, y, width, height } = display.bounds;
                this.win.setBounds({ x, y, width, height });
                this.win.setFullScreen(true);
            }
        }));

        const roomItems = socketManager.clientGuilds.length > 0
            ? socketManager.clientGuilds.map(guild => ({
                label: guild.name,
                type: 'checkbox',
                checked: configManager.activeRooms.has(guild.id),
                click: () => this.toggleRoom(guild.id)
            }))
            : [{ label: 'Aucune room disponible', enabled: false }];

        const template = [
            { label: configManager.userId ? `Connecté: ${configManager.userId}` : 'Non connecté', enabled: false },
            {
                label: 'Se connecter à Discord',
                enabled: !!socketManager.botClientId && !configManager.userId,
                visible: !configManager.userId,
                click: () => {
                    const redirectUri = encodeURIComponent(`http://iceboxer.hd.free.fr:8080/callback`);
                    const authUrl = `https://discord.com/api/oauth2/authorize?client_id=${socketManager.botClientId}&redirect_uri=${redirectUri}&response_type=code&scope=identify%20guilds`;
                    shell.openExternal(authUrl);
                }
            },
            {
                label: 'Recharger la liste des serveurs',
                enabled: !!configManager.userId,
                click: () => socketManager.getMyGuilds()
            },
            {
                label: 'Se déconnecter',
                visible: !!configManager.userId,
                click: () => {
                    configManager.logout();
                    socketManager.clientGuilds = []; // On vide la liste locale
                    this.updateMenu();
                }
            },
            {
                label: 'DÉBOGAGE : Simuler Auth (ID 324189371052064768)',
                visible: !configManager.userId,
                click: () => {
                    console.log("Simulation d'authentification ID 324189371052064768...");
                    configManager.setUserId("324189371052064768");
                    socketManager.getMyGuilds();
                    this.updateMenu();
                }
            },
            { type: 'separator' },
            { label: 'Style : Fullscreen', click: () => this.win.webContents.send('set-class', 'fullscreen') },
            { label: 'Style : Illustration', click: () => this.win.webContents.send('set-class', 'illustration') },
            { type: 'separator' },
            { label: 'Tests médias :', enabled: false },
            {
                label: 'Test : Image (Antonin)',
                click: () => {
                    const localPath = path.resolve(__dirname, '../../assets/bureau_homosexuel.png');
                    this.win.webContents.send('update-media', {
                        url: `file://${localPath}`,
                        type: 'image',
                        text: "Je peux voir ta mère ?",
                        duration: 2000
                    });
                }
            },
            {
                label: 'Test : Vidéo',
                click: () => {
                    const localPath = path.resolve(__dirname, '../../assets/dont_care_im_diogenemaxxing.mp4');
                    this.win.webContents.send('update-media', {
                        url: `file://${localPath}`,
                        type: 'video',
                        text: "Mehdi de Thèbes"
                    });
                }
            },
            { type: 'separator' },
            { label: 'Choisir l\'écran :', enabled: false },
            ...displayItems,
            { type: 'separator' },
            { label: 'Rooms disponibles :', enabled: false },
            ...roomItems,
            { type: 'separator' },
            { label: 'Quitter', click: () => app.quit() }
        ];

        const contextMenu = Menu.buildFromTemplate(template);
        this.tray.setContextMenu(contextMenu);
    }

    toggleRoom(guildId) {
        const isActive = configManager.toggleRoom(guildId);
        if (isActive) {
            socketManager.joinRoom(guildId);
        } else {
            socketManager.leaveRoom(guildId);
        }
        this.updateMenu();
    }
}

module.exports = new TrayManager();
