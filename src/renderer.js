const { ipcRenderer } = require('electron');

const imgTag = document.getElementById('image_container');
const videoTag = document.getElementById('video_container');
const subtitleTag = document.getElementById('subtitle_container');
const audioTag = document.getElementById('audio_container');

let Timer = null;

/**
 * Calcule la taille de police optimale pour macOS/Windows
 */
function getOptimalFontSize(text, maxWidth, maxHeight) {
    const tester = document.createElement('div');
    tester.className = 'offscreen-test';
    tester.style.position = 'absolute';
    tester.style.visibility = 'hidden';
    tester.style.whiteSpace = 'pre-wrap'; // Important pour le multi-ligne
    tester.style.width = maxWidth + 'px';
    // Police système standard sur Mac (San Francisco) et Windows (Segoe UI)
    tester.style.fontFamily = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    tester.style.fontWeight = "bold";
    tester.style.lineHeight = "1.1";
    tester.innerText = text;
    document.body.appendChild(tester);

    let fontSize = 150;

    while (fontSize > 15) {
        tester.style.fontSize = fontSize + 'px';
        if (tester.scrollHeight <= maxHeight && tester.scrollWidth <= maxWidth) {
            break;
        }
        fontSize--;
    }

    document.body.removeChild(tester);
    return fontSize;
}

function hideAllMedia() {
    imgTag.style.display = 'none';
    videoTag.style.display = 'none';

    [videoTag, audioTag].forEach(el => {
        el.pause();
        el.src = "";
        el.load(); // Force la libération des ressources sur Mac
    });

    imgTag.src = "";
    subtitleTag.innerText = "";

    if (Timer) {
        clearTimeout(Timer);
        Timer = null;
    }
}

// Sécurité pour l'autoplay sur macOS
[videoTag, audioTag].forEach(tag => {
    tag.addEventListener('ended', () => hideAllMedia());
});

ipcRenderer.on('stop', () => {
    hideAllMedia();
});

ipcRenderer.on('set-class', (event, className) => {
    [imgTag, videoTag].forEach(el => {
        el.classList.remove('fullscreen', 'illustration');
        el.classList.add(className);
    });
});

ipcRenderer.on('update-media', (event, data) => {
    hideAllMedia();

    const isVideo = (data.url && data.type === 'video');
    const isAudio = (data.url && data.type === 'audio');

    if (data.text) {
        const container = document.getElementById('subtitle_container');
        container.style.visibility = 'hidden';

        // Sur macOS, les dimensions peuvent mettre quelques ms à se stabiliser
        const bestSize = getOptimalFontSize(
            data.text,
            container.clientWidth || window.innerWidth * 0.9,
            container.clientHeight || window.innerHeight * 0.3
        );

        container.style.fontSize = bestSize + 'px';
        container.innerText = data.text;
        container.style.visibility = 'visible';
    }

    if (data.url) {
        // macOS est strict sur les URLs file://, on s'assure qu'elles sont bien formées
        const mediaUrl = data.url;

        if (isVideo) {
            videoTag.src = mediaUrl;
            videoTag.style.display = 'block';
            videoTag.play().catch(err => console.error("Erreur lecture vidéo:", err));
        } else if (isAudio) {
            audioTag.src = mediaUrl;
            audioTag.play().catch(err => console.error("Erreur lecture audio:", err));
        } else if (data.type === 'image') {
            imgTag.src = mediaUrl;
            imgTag.onload = () => { imgTag.style.display = 'block'; };
            imgTag.onerror = () => { console.error("Erreur chargement image:", mediaUrl); };
        }
    }

    if (!isVideo && !isAudio && data.duration) {
        Timer = setTimeout(() => {
            hideAllMedia();
        }, data.duration);
    }
});

/**
 * ATTENTION : Vous aviez du code Socket.io ici.
 * Dans votre architecture, la Socket est gérée dans MAIN.JS.
 * Si vous voulez afficher une liste de serveurs dans le HTML (index.html),
 * vous devez envoyer les données du Main vers le Renderer via ipcRenderer.send/on.
 * * Si votre interface est purement un Tray (menu contextuel),
 * ce code ci-dessous est inutile dans renderer.js.
 */