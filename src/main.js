const { app, BrowserWindow, Tray, Menu, nativeImage, screen, shell, protocol } = require('electron');
const path = require('node:path');
const { io } = require("socket.io-client");
const fs = require('node:fs');
const CONFIG_PATH = path.join(app.getPath('userData'), 'configLiveChat.json');
const dotenv = require("dotenv");

dotenv.config();

const socket = io(`${process.env.ADDRESS}:8080`);

let win = null;
let tray = null;
let activeRooms = new Set();
let userId = null;
let clientGuilds = [];
let botClientId = null;

function saveConfig() {
    const config = {
        userId: userId,
        activeRooms: Array.from(activeRooms) // On transforme le Set en Tableau
    };
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config));
}

function loadConfig() {
    if (fs.existsSync(CONFIG_PATH)) {
        const data = JSON.parse(fs.readFileSync(CONFIG_PATH));
        userId = data.userId || null;
        activeRooms = new Set(data.activeRooms || []);
        return true;
    }
    return false;
}

const isPrimaryInstance = app.requestSingleInstanceLock();

if (!isPrimaryInstance) {
    // Si c'est une deuxième instance, on ferme immédiatement
    app.quit();
} else {
    // Si c'est l'instance principale, on écoute les tentatives d'ouverture d'une 2ème instance
    app.on('second-instance', (event, commandLine) => {
        // Quelqu'un a essayé de lancer une deuxième instance (probablement le lien OAuth)
        if (win) {
            if (win.isMinimized()) win.restore();
            win.focus();
        }

        // On récupère l'URL dans les arguments de la ligne de commande (Windows/Linux)
        const url = commandLine.pop();
        handleAuthUrl(url);
    });

    // --- GESTION DU PROTOCOLE (DEEP LINKING) ---
    if (process.defaultApp) {
        if (process.argv.length >= 2) {
            app.setAsDefaultProtocolClient('electron-app', process.execPath, [path.resolve(process.argv[1])]);
        }
    } else {
        app.setAsDefaultProtocolClient('electron-app');
    }
}

// Fonction centralisée pour traiter l'URL d'auth
function handleAuthUrl(url) {
    try {
        const urlObj = new URL(url);
        if (urlObj.hostname === 'auth') {
            userId = urlObj.searchParams.get('id');
            console.log("ID reçu via protocole :", userId);

            if (userId && socket.connected) {
                socket.emit("get-my-guilds", userId);
                updateTrayMenu();
            }
        }
    } catch (e) {
        console.error("URL invalide :", url);
    }
}

// Garde aussi cet événement pour macOS
app.on('open-url', (event, url) => {
    event.preventDefault();
    handleAuthUrl(url);
});

// --- FENÊTRE PRINCIPALE ---
function createWindow() {
    win = new BrowserWindow({
        fullscreen: true,
        resizable: false,
        transparent: true,
        alwaysOnTop: true,
        focusable: false,
        skipTaskbar: true,
        frame: false,
        titleBarStyle: 'hidden',
        type: 'panel',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false,
        }
    });

    if (process.platform === 'darwin') {
        win.setAlwaysOnTop(true, 'screen-saver');
        win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    }

    win.setIgnoreMouseEvents(true);
    win.loadFile('./src/index.html');

    win.once('ready-to-show', () => {
        // On affiche sans prendre le focus
        win.showInactive(); 
    });
}

// --- GESTION DU MENU TRAY ---
function updateTrayMenu() {
    const displays = screen.getAllDisplays();

    // Éléments du menu pour les écrans
    const displayItems = displays.map((display, index) => ({
        label: `Écran ${index + 1}: ${display.label}`,
        type: 'radio',
        checked: win ? win.getBounds().x === display.bounds.x : index === 0,
        click: () => {
            const { x, y, width, height } = display.bounds;
            win.setBounds({ x, y, width, height });
            win.setFullScreen(true);
        }
    }));

    // Éléments du menu pour les rooms (serveurs)
    const roomItems = clientGuilds.length > 0
        ? clientGuilds.map(guild => ({
            label: guild.name,
            type: 'checkbox',
            checked: activeRooms.has(guild.id),
            click: () => toggleRoom(guild.id)
        }))
        : [{ label: 'Aucune room disponible', enabled: false }];

    const template = [
        { label: userId ? `Connecté: ${userId}` : 'Non connecté', enabled: false },
        {
            label: 'Se connecter à Discord',
            // On désactive le bouton tant qu'on n'a pas reçu l'ID du bot
            enabled: !!botClientId && !userId,
            visible: !userId,
            click: () => {
                if (!botClientId) return;

                // ON CONSTRUIT L'URL DYNAMIQUEMENT ICI
                const redirectUri = encodeURIComponent(`${process.env.ADDRESS}:8080/callback`);
                const authUrl = `https://discord.com/api/oauth2/authorize?client_id=${botClientId}&redirect_uri=${redirectUri}&response_type=code&scope=identify%20guilds`;

                shell.openExternal(authUrl);
            }
        },
        {
            label: 'Recharger la liste des serveurs',
            enabled: !!userId, // Actif seulement si on est connecté
            click: () => {
                console.log("Rechargement des serveurs...");
                socket.emit("get-my-guilds", userId);
            }
        },
        { type: 'separator' },
        { label: 'Style : Fullscreen', click: () => win.webContents.send('set-class', 'fullscreen') },
        { label: 'Style : Illustration', click: () => win.webContents.send('set-class', 'illustration') },
        { type: 'separator' },
        { label: 'Tests médias :', enabled: false },
        {
            label: 'Test : Image (Antonin)',
            click: () => {
                const localPath = path.resolve(__dirname, '../assets/bureau_homosexuel.png');

                win.webContents.send('update-media', {
                    url: `file://${localPath}`,
                    type: 'image',
                    text: "Je peux voir ta mère ?",
                    duration: 2000
                },);
            }
        },
        {
            label: 'Test : Image (Romain)',
            click: () => {
                const localPath = path.resolve(__dirname, '../assets/icons/romain_guillon.jpg');

                win.webContents.send('update-media', {
                    url: `file://${localPath}`,
                    type: 'image',
                    text: "mec super moche",
                    duration: 2000
                });
            }
        },
        {
            label: 'Test : Vidéo',
            click: () => {
                const localPath = path.resolve(__dirname, '../assets/dont_care_im_diogenemaxxing.mp4');

                win.webContents.send('update-media', {
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
    tray.setContextMenu(contextMenu);
}

// --- FONCTIONS UTILES ---
function toggleRoom(guildId) {
    if (activeRooms.has(guildId)) {
        activeRooms.delete(guildId);
        socket.emit("leave-server-room", guildId); // On informe le bot qu'on quitte
    } else {
        activeRooms.add(guildId);
        socket.emit("join-server-room", guildId); // On informe le bot qu'on rejoint
    }

    saveConfig();
    updateTrayMenu(); // Rafraîchir l'affichage des coches
}

// --- ÉVÉNEMENTS APP ---
app.whenReady().then(() => {
    loadConfig();
    createWindow();

    const iconPath = path.join(__dirname, '../assets/icons/romain_guillon.jpg');
    tray = new Tray(nativeImage.createFromPath(iconPath));
    tray.setToolTip('LiveChat-Desktop');

    updateTrayMenu();

    screen.on('display-added', updateTrayMenu);
    screen.on('display-removed', updateTrayMenu);
});

socket.on("connect", () => {
    console.log("Connecté au serveur Socket");
    if (userId) {
        socket.emit("get-my-guilds", userId);
        // Les rooms seront rejointes automatiquement via l'évenement list-guilds
    }
});

socket.on("bot-config", (config) => {
    console.log("Config reçue du bot :", config);
    botClientId = config.clientId;
    updateTrayMenu(); // On rafraîchit le menu pour activer le bouton "Se connecter"
});

// --- COMMUNICATION SOCKET ---
socket.on("list-guilds", (guilds) => {
    clientGuilds = guilds;
    activeRooms.forEach(roomId => {
        // On vérifie si le serveur est toujours dans la liste du bot
        if (guilds.some(g => g.id === roomId)) {
            socket.emit("join-server-room", roomId);
        } else {
            activeRooms.delete(roomId); // Le bot n'est plus sur ce serveur
        }
    });

    saveConfig();
    updateTrayMenu(); // On met à jour le menu quand on reçoit la liste
});

socket.on("display-media", (data) => {
    if (win) {
        win.webContents.send('set-class', data.format);
        win.webContents.send('update-media', data);
    }
});

socket.on("stop", () => {
    if (win) win.webContents.send('stop');
});

app.on('window-all-closed', () => app.quit());