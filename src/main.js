const { app, BrowserWindow, Tray, Menu, nativeImage, screen, shell } = require('electron');
const path = require('node:path');
const { io } = require("socket.io-client");
const fs = require('node:fs');
const dotenv = require("dotenv");

dotenv.config();

// Chemins et variables globales
const CONFIG_PATH = path.join(app.getPath('userData'), 'configLiveChat.json');
const socket = io(`http://iceboxer.hd.free.fr:8080`);

let win = null;
let tray = null;
let activeRooms = new Set();
let userId = null;
let clientGuilds = [];
let botClientId = null;
let pendingUrl = null; // Stocke l'URL d'auth si l'app n'est pas encore prête

// --- PERSISTANCE ---
function saveConfig() {
    const config = {
        userId: userId,
        activeRooms: Array.from(activeRooms)
    };
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config));
}

function loadConfig() {
    if (fs.existsSync(CONFIG_PATH)) {
        try {
            const data = JSON.parse(fs.readFileSync(CONFIG_PATH));
            userId = data.userId || null;
            activeRooms = new Set(data.activeRooms || []);
            return true;
        } catch (e) {
            console.error("Erreur lecture config:", e);
        }
    }
    return false;
}

// --- GESTION DU PROTOCOLE (DEEP LINKING) ---
if (process.defaultApp) {
    if (process.argv.length >= 2) {
        app.setAsDefaultProtocolClient('electron-app', process.execPath, [path.resolve(process.argv[1])]);
    }
} else {
    app.setAsDefaultProtocolClient('electron-app');
}

// Fonction centralisée pour traiter l'URL d'authentification
function handleAuthUrl(url) {
    if (!url) return;
    try {
        const urlObj = new URL(url);
        if (urlObj.hostname === 'auth') {
            userId = urlObj.searchParams.get('id');
            console.log("ID reçu :", userId);

            if (userId && socket.connected) {
                socket.emit("get-my-guilds", userId);
            }
            updateTrayMenu();
            saveConfig();
        }
    } catch (e) {
        console.error("URL invalide ou malformée :", url);
    }
}

// --- LOGIQUE D'INSTANCE UNIQUE ---
const isPrimaryInstance = app.requestSingleInstanceLock();

if (!isPrimaryInstance) {
    app.quit();
} else {
    // Événement Windows/Linux
    app.on('second-instance', (event, commandLine) => {
        if (win) {
            if (win.isMinimized()) win.restore();
            win.focus();
        }
        const url = commandLine.pop();
        handleAuthUrl(url);
    });

    // Événement macOS (Deep Linking)
    app.on('open-url', (event, url) => {
        event.preventDefault();
        if (app.isReady()) {
            handleAuthUrl(url);
        } else {
            pendingUrl = url;
        }
    });
}

// --- FENÊTRE PRINCIPALE ---
function createWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.bounds;

    win = new BrowserWindow({
        width: width,
        height: height,
        transparent: true,
        alwaysOnTop: true,
        focusable: false,
        skipTaskbar: false,
        frame: false,
        type: 'panel', // Nécessaire pour macOS
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false,
        }
    });

    // Configuration spécifique macOS pour le mode "Overlay"
    if (process.platform === 'darwin') {
        win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
        win.setAlwaysOnTop(true, 'screen-saver');
        win.setIgnoreMouseEvents(true, { forward: true });
    } else {
        win.setIgnoreMouseEvents(true);
        win.setFullScreen(true);
    }

    win.loadFile(path.join(__dirname, 'index.html'));
    win.once('ready-to-show', () => {
        win.showInactive();
    });
}

// --- MENU TRAY ---
function updateTrayMenu() {
    if (!tray) return;

    const displays = screen.getAllDisplays();
    const displayItems = displays.map((display, index) => ({
        label: `Écran ${index + 1}: ${display.label}`,
        type: 'radio',
        checked: win ? win.getBounds().x === display.bounds.x : index === 0,
        click: () => {
            const { x, y, width, height } = display.bounds;
            win.setBounds({ x, y, width, height });
            if (process.platform !== 'darwin') win.setFullScreen(true);
        }
    }));

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
            enabled: !!botClientId && !userId,
            visible: !userId,
            click: () => {
                const redirectUri = encodeURIComponent(`http://iceboxer.hd.free.fr:8080/callback`);
                const authUrl = `https://discord.com/api/oauth2/authorize?client_id=${botClientId}&redirect_uri=${redirectUri}&response_type=code&scope=identify%20guilds`;
                shell.openExternal(authUrl);
            }
        },
        {
            label: 'Déconnexion',
            visible: !!userId,
            click: () => {
                userId = null;
                activeRooms.clear();
                saveConfig();
                updateTrayMenu();
            }
        },
        { type: 'separator' },
        { label: 'Recharger les serveurs', enabled: !!userId, click: () => socket.emit("get-my-guilds", userId) },
        { type: 'separator' },
        { label: 'Style : Fullscreen', click: () => win.webContents.send('set-class', 'fullscreen') },
        { label: 'Style : Illustration', click: () => win.webContents.send('set-class', 'illustration') },
        { type: 'separator' },
        { label: 'Choisir l\'écran :', enabled: false },
        ...displayItems,
        { type: 'separator' },
        { label: 'Rooms (Serveurs) :', enabled: false },
        ...roomItems,
        { type: 'separator' },
        { label: 'Quitter', click: () => app.quit() }
    ];

    tray.setContextMenu(Menu.buildFromTemplate(template));
}

function toggleRoom(guildId) {
    if (activeRooms.has(guildId)) {
        activeRooms.delete(guildId);
        socket.emit("leave-server-room", guildId);
    } else {
        activeRooms.add(guildId);
        socket.emit("join-server-room", guildId);
    }
    saveConfig();
    updateTrayMenu();
}

if (process.platform === 'darwin') {
    app.commandLine.appendSwitch('disable-features', 'LayoutServiceColorSubpixel');
}
// --- INITIALISATION ---
app.whenReady().then(() => {
    loadConfig();

    createWindow();

    // Utilisation d'une icône "Template" pour macOS
    const iconPath = path.join(__dirname, '../assets/icons/template_romain_guillon.jpg');
    const icon = nativeImage.createFromPath(iconPath).resize({ width: 18, height: 18 });
    icon.setTemplateImage(true);

    tray = new Tray(icon);
    tray.setToolTip('LiveChat-Desktop');

    updateTrayMenu();

    if (pendingUrl) {
        handleAuthUrl(pendingUrl);
        pendingUrl = null;
    }

    screen.on('display-added', updateTrayMenu);
    screen.on('display-removed', updateTrayMenu);
});

// --- SOCKETS ---
socket.on("connect", () => {
    console.log("Connecté au serveur Socket");
    if (userId) socket.emit("get-my-guilds", userId);
});

socket.on("bot-config", (config) => {
    botClientId = config.clientId;
    updateTrayMenu();
});

socket.on("list-guilds", (guilds) => {
    clientGuilds = guilds;
    activeRooms.forEach(roomId => {
        if (guilds.some(g => g.id === roomId)) {
            socket.emit("join-server-room", roomId);
        } else {
            activeRooms.delete(roomId);
        }
    });
    saveConfig();
    updateTrayMenu();
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

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});