const imgTag = document.getElementById('image_container');
const videoTag = document.getElementById('video_container');
const subtitleTag = document.getElementById('subtitle_container');
const audioTag = document.getElementById('audio_container');
const webTag = document.getElementById('web_container');

let Timer = null;

function getOptimalFontSize(text, maxWidth, maxHeight) {
    const tester = document.createElement('div');
    tester.className = 'offscreen-test';
    tester.style.width = maxWidth + 'px';
    tester.style.fontFamily = "'Segoe UI', sans-serif";
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
    webTag.style.display = 'none';

    [videoTag, audioTag].forEach(el => {
        el.pause();
        el.src = "";
    });

    imgTag.src = "";
    subtitleTag.innerText = "";
    subtitleTag.style.visibility = 'hidden';

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

// Utilisation de l'API exposée par le preload script
if (window.electronAPI) {
    window.electronAPI.onStop(() => {
        hideAllMedia();
    });

    window.electronAPI.onSetClass((className) => {
        [imgTag, videoTag, webTag].forEach(el => {
            el.classList.remove('fullscreen', 'illustration');
            el.classList.add(className);
        });
        console.log(`Style appliqué : ${className}`);
    });

    window.electronAPI.onUpdateMedia((data) => {
        hideAllMedia();

        const isVideo = (data.url && data.type === 'video');
        const isAudio = (data.url && data.type === 'audio');

        const startTimer = (ms) => {
            if (Timer) clearTimeout(Timer);
            Timer = setTimeout(() => {
                hideAllMedia();
            }, ms);
        };

        // 1. GESTION DU TEXTE
        if (data.text) {
            subtitleTag.style.visibility = 'hidden';
            const bestSize = getOptimalFontSize(data.text, subtitleTag.clientWidth, subtitleTag.clientHeight);
            subtitleTag.style.fontSize = bestSize + 'px';
            subtitleTag.innerText = data.text;
            subtitleTag.style.visibility = 'visible';

            if (!data.url && !data.lien && data.duration) {
                startTimer(data.duration);
            }
        }

        // 2. GESTION DES MÉDIAS (Image, Vidéo, Audio)
        if (data.url) {
            console.log("Tentative de chargement du média :", data.url);

            if (isVideo) {
                videoTag.onerror = (e) => console.error("Erreur VideoTag :", videoTag.error);
                videoTag.onplay = () => {
                    console.log("Lecture vidéo démarrée");
                    videoTag.style.display = 'block';
                };

                videoTag.src = data.url;
                videoTag.play().catch(err => console.error("Erreur play() :", err));
            } else if (isAudio) {
                audioTag.src = data.url;
                audioTag.play().catch(err => console.error("Erreur audio play() :", err));
            } else if (data.type === 'image') {
                imgTag.onload = () => {
                    imgTag.style.display = 'block';
                    if (data.duration) startTimer(data.duration);
                };
                imgTag.src = data.url;
            }
        }

        // 3. GESTION DU LIEN (Webview/Iframe)
        if (data.lien) {
            webTag.onload = () => {
                webTag.style.display = 'block';
                if (data.duration && !data.url) startTimer(data.duration);
            };
            webTag.src = data.lien;
        }
    });
}
