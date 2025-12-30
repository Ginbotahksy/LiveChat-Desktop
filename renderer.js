const { ipcRenderer } = require('electron');

const imgTag = document.getElementById('image_container');
const videoTag = document.getElementById('video_container');
const subtitleTag = document.getElementById('subtitle_container');
const audioTag = document.getElementById('audio_container');

let Timer = null;

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
        subtitleTag.innerText = data.text;
        subtitleTag.style.display = 'block';
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
