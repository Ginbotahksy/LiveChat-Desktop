const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onUpdateMedia: (callback) => ipcRenderer.on('update-media', (_event, value) => callback(value)),
    onStop: (callback) => ipcRenderer.on('stop', (_event) => callback()),
    onSetClass: (callback) => ipcRenderer.on('set-class', (_event, value) => callback(value)),
    // On pourrait ajouter d'autres méthodes ici si besoin
});
