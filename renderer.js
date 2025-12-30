const { ipcRenderer } = require('electron');

const imgTag = document.getElementById('image_container');
const videoTag = document.getElementById('video_container');
const subtitleTag = document.getElementById('subtitle_container');
const audioTag = document.getElementById('audio_container');

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
    imgTag.style.display = 'none';
    videoTag.style.display = 'none';

    [videoTag, audioTag].forEach(el => {
        el.pause();
        el.src = "";
    });

    videoTag.src = "";
    imgTag.src = "";
    subtitleTag.innerText = "";

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
    [imgTag, videoTag].forEach(el => {
        el.classList.remove('fullscreen', 'illustration');
        el.classList.add(className);
    });
    console.log(`Style appliqué : ${className}`);
});

ipcRenderer.on('update-media', (event, data) => {
    hideAllMedia();

    const isVideo = (data.url && data.type === 'video');
    const isAudio = (data.url && data.type === 'audio');

    if (data.text) {
        const container = document.getElementById('subtitle_container');
        
        // 1. On cache le conteneur pendant qu'on prépare
        container.style.visibility = 'hidden';

        // 2. On calcule la taille optimale hors-écran
        const bestSize = getOptimalFontSize(
            data.text, 
            container.clientWidth, 
            container.clientHeight
        );

        // 3. On applique tout d'un coup (Texte + Taille)
        container.style.fontSize = bestSize + 'px';
        container.innerText = data.text;

        // 4. On rend visible : le texte apparaît déjà à la bonne taille
        container.style.visibility = 'visible';
    }

    if (data.url) {
        if (isVideo) {
            videoTag.src = data.url;
            videoTag.style.display = 'block';
            videoTag.play();
        } else if (isAudio) {
            audioTag.src = data.url;
            audioTag.play();
        } else if (data.type === 'image') {
            imgTag.src = data.url;
            imgTag.onload = () => { imgTag.style.display = 'block'; };
        }
    }

    if (!isVideo && !isAudio && data.duration) {
        Timer = setTimeout(() => {
            hideAllMedia();
        }, data.duration);
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
