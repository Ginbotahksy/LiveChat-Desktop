const { ipcRenderer } = require('electron');

const imgTag = document.getElementById('image_container');
const videoTag = document.getElementById('video_container');
const subtitleTag = document.getElementById('subtitle_container');
const audioTag = document.getElementById('audio_container');
const webTag = document.getElementById('web_container');

let Timer = null;

function getOptimalFontSize(text, maxWidth, maxHeight) {
    // On crée un élément temporaire identique au conteneur
    const tester = document.createElement('div');
    tester.className = 'offscreen-test';
    tester.style.width = maxWidth + 'px';
    tester.style.fontFamily = "'Segoe UI', sans-serif";
    tester.style.fontWeight = "bold";
    tester.style.lineHeight = "1.1";
    tester.innerText = text;
    document.body.appendChild(tester);

    let fontSize = 150; // Taille max

    // Boucle de réduction de taille
    while (fontSize > 15) {
        tester.style.fontSize = fontSize + 'px';
        // Si le texte rentre dans les dimensions
        if (tester.scrollHeight <= maxHeight && tester.scrollWidth <= maxWidth) {
            break;
        }
        fontSize--;
    }

    // On nettoie le DOM
    document.body.removeChild(tester);
    return fontSize;
}

function hideAllMedia() {
    imgTag.style.display = 'none';
    videoTag.style.display = 'none';
    webTag.style.display = 'none';

    [videoTag, audioTag].forEach(el => {
        el.pause();
        el.src = "";
    });

    videoTag.src = "";
    imgTag.src = "";
    subtitleTag.innerText = "";

    try {
        if (webTag.getAttribute('src') !== "about:blank") {
            webTag.src = "about:blank";
        }
    } catch (e) { }

    if (Timer) {
        clearTimeout(Timer);
        Timer = null;
    }
}

[videoTag, audioTag].forEach(tag => {
    tag.addEventListener('ended', () => hideAllMedia());
});

ipcRenderer.on('stop', () => {
    hideAllMedia();
});

ipcRenderer.on('set-class', (event, className) => {
    [imgTag, videoTag, webTag].forEach(el => {
        el.classList.remove('fullscreen', 'illustration');
        el.classList.add(className);
    });
    console.log(`Style appliqué : ${className}`);
});

ipcRenderer.on('update-media', (event, data) => {
    hideAllMedia();

    const isVideo = (data.url && data.type === 'video');
    const isAudio = (data.url && data.type === 'audio');

    const startTimer = (ms) => {
        if (Timer) clearTimeout(Timer);
        Timer = setTimeout(() => {
            hideAllMedia();
        }, ms);
    };

    // 1. GESTION DU TEXTE (Immédiat)
    if (data.text) {
        const container = document.getElementById('subtitle_container');
        container.style.visibility = 'hidden';
        const bestSize = getOptimalFontSize(data.text, container.clientWidth, container.clientHeight);
        container.style.fontSize = bestSize + 'px';
        container.innerText = data.text;
        container.style.visibility = 'visible';

        // Si c'est du texte seul (pas de média, pas de lien), on lance le timer de suite
        if (!data.url && !data.lien && data.duration) {
            startTimer(data.duration);
        }
    }

    // 2. GESTION DES MÉDIAS (Image, Vidéo, Audio)
    if (data.url) {
        if (isVideo) {
            videoTag.oncanplay = () => {
                videoTag.style.display = 'block';
                // Le timer de la vidéo est géré par l'event 'ended', 
                // mais on peut mettre un fallback de sécurité avec data.duration
            };
            videoTag.src = data.url;
            videoTag.play();
        } else if (isAudio) {
            audioTag.src = data.url;
            audioTag.play();
        } else if (data.type === 'image') {
            imgTag.onload = () => {
                imgTag.style.display = 'block';
                if (data.duration) startTimer(data.duration); // On lance quand l'image est chargée
            };
            imgTag.src = data.url;
        }
    }

    // 3. GESTION DU LIEN (Webview)
    if (data.lien) {
         webTag.onload = () => {
            webTag.style.display = 'block';
            if ((data.duration) && !data.url) startTimer(data.duration);
        };

        webTag.src = data.lien;
    }
});

// Demander les serveurs au bot
socket.emit("get-my-guilds", userId);

// Recevoir la liste et créer les boutons/options
socket.on("list-guilds", (guilds) => {
    const select = document.getElementById("server-select");
    guilds.forEach(guild => {
        let opt = document.createElement("option");
        opt.value = guild.id;
        opt.innerHTML = guild.name;
        select.appendChild(opt);
    });
});
