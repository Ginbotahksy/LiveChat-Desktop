const { shell, protocol } = require('electron');

// URL de connexion Discord (à générer sur le portail développeur avec les scopes identify et guilds)
const authUrl = "https://discord.com/api/oauth2/authorize?client_id=...&response_type=code&scope=identify%20guilds";

function openAuthWindow() {
    shell.openExternal(authUrl);
}

// Enregistrement du protocole electron-app://
app.setAsDefaultProtocolClient('electron-app');

app.on('open-url', (event, url) => {
    const urlObj = new URL(url);
    if (urlObj.hostname === 'auth') {
        const userId = urlObj.searchParams.get('id');
        console.log("Utilisateur authentifié :", userId);
        
        // On sauvegarde l'ID et on demande les serveurs au Bot
        socket.emit("get-my-guilds", userId);
    }
});