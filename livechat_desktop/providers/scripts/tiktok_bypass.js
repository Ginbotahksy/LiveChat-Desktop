// Masquer les bandeaux avec CSS au cas où on n'arrive pas à cliquer
const style = document.createElement('style');
style.innerHTML = '.tiktok-cookie-banner, [data-testid="CookieConsent"], ytd-consent-bump-v2-lightbox, .tp-yt-paper-dialog { display: none !important; }';
document.head.appendChild(style);

// Boucle agressive pour cliquer sur les popups asynchrones
let attempts = 0;
const intervalId = setInterval(() => {
    attempts++;
    // On cherche tous les éléments cliquables
    document.querySelectorAll('button, a, div[role="button"]').forEach(btn => {
        const text = (btn.innerText || '').toLowerCase();
        if (text.includes('allow all') || text.includes('tout accepter') || 
            text.includes('decline') || text.includes('refuser') || text.includes('accepter cookies')) {
            btn.click();
        }
    });
    
    // Clic sur Play
    const playBtn = document.querySelector('.xgplayer-play, .play-button, button[aria-label="Play"], button[aria-label="Watch"]');
    if (playBtn) { 
        playBtn.click(); 
    }
    
    // On arrête de spammer après 20 essais (10 secondes)
    if (attempts > 20) clearInterval(intervalId);
}, 500);
