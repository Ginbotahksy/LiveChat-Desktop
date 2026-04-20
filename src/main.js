const { app, BrowserWindow, screen, session } = require('electron');
const path = require('node:path');
const dotenv = require("dotenv");

// Diagnostic : On affiche TOUT ce que l'application reçoit au lancement
console.log("=== DIAGNOSTIC DÉMARRAGE ===");
console.log("Arguments (argv) :", process.argv);
console.log("Chemin exécution :", process.execPath);
console.log("Dossier courant :", process.cwd());
console.log("============================");

app.setName('livechat-desktop');
dotenv.config();

const configManager = require("./modules/configManager");
const socketManager = require("./modules/socketManager");
const trayManager = require("./modules/trayManager");

let win = null;

function handleAuthUrl(url) {
    if (!url) return;
    console.log(">>> ANALYSE DE L'URL REÇUE :", url);

    try {
        const idMatch = url.match(/[?&]id=([^&"']+)/);
        const userId = idMatch ? idMatch[1] : null;

        if (userId) {
            console.log(">>> ID DÉTECTÉ AVEC SUCCÈS :", userId);
            configManager.setUserId(userId);
            socketManager.getMyGuilds();
            trayManager.updateMenu();
        } else {
            console.warn(">>> ANALYSE : Aucun ID trouvé dans cette chaîne.");
        }
    } catch (e) {
        console.error(">>> ERREUR ANALYSE :", e.message);
    }
}

// --- GESTION DE L'INSTANCE UNIQUE ---
const gotLock = app.requestSingleInstanceLock();

if (!gotLock) {
    console.log("!!! Instance secondaire : Envoi des arguments à l'instance principale et fermeture.");
    app.quit();
} else {
    app.on('second-instance', (event, commandLine) => {
        console.log("=== SIGNAL SECONDE INSTANCE REÇU ===");
        console.log("Arguments reçus :", commandLine);
        
        if (win) {
            if (win.isMinimized()) win.restore();
        }

        const url = commandLine.find(arg => arg.includes('electron-app://'));
        if (url) {
            handleAuthUrl(url);
        } else {
            console.log("!!! Aucun lien de protocole trouvé dans les arguments de la seconde instance.");
        }
        console.log("=====================================");
    });

    if (process.defaultApp) {
        if (process.argv.length >= 2) {
            app.setAsDefaultProtocolClient('electron-app', process.execPath, [path.resolve(process.argv[1])]);
        }
    } else {
        app.setAsDefaultProtocolClient('electron-app');
    }
}

function createWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height, x, y } = primaryDisplay.bounds;

    win = new BrowserWindow({
        width: width,
        height: height,
        x: x,
        y: y,
        resizable: false,
        transparent: true,
        alwaysOnTop: true,
        focusable: false,
        skipTaskbar: true,
        frame: false,
        type: process.platform === 'linux' ? 'toolbar' : 'panel',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            webSecurity: false,
        }
    });

    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
        let responseHeaders = details.responseHeaders;
        const headersToDrop = ['x-frame-options', 'content-security-policy', 'x-content-security-policy', 'frame-options'];
        Object.keys(responseHeaders).forEach(h => { if (headersToDrop.includes(h.toLowerCase())) delete responseHeaders[h]; });
        callback({ cancel: false, responseHeaders });
    });

    win.setAlwaysOnTop(true, 'screen-saver');
    win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    win.setIgnoreMouseEvents(true, { forward: false });
    win.setFocusable(false);
    win.loadFile(path.join(__dirname, 'index.html'));

    win.webContents.on('did-finish-load', () => {
        win.webContents.send('set-class', 'illustration');
        // win.webContents.openDevTools({ mode: 'detach' }); // DÉBOGAGE ACTIF
        
        // Vérification des arguments au démarrage
        const url = process.argv.find(arg => arg.includes('electron-app://'));
        if (url) {
            console.log(">>> URL détectée dès le démarrage (argv)");
            handleAuthUrl(url);
        }
    });

    win.once('ready-to-show', () => win.showInactive());
}

app.whenReady().then(() => {
    configManager.loadConfig();
    createWindow();
    socketManager.init(win, () => trayManager.updateMenu());
    trayManager.init(win);
});

app.on('open-url', (event, url) => {
    event.preventDefault();
    console.log("=== ÉVÉNEMENT OPEN-URL ===");
    handleAuthUrl(url);
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
