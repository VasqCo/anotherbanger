let currentSection = 1;
let currentMeasure = 1;
let sectionPlayCount = 0;
let isPlaying = false;

function getBaseUrl() {
    return window.SITE_CONFIG && window.SITE_CONFIG.baseUrl ? window.SITE_CONFIG.baseUrl : '';
}

function playThresholdAudio() {
    if (isPlaying) return;
    const baseUrl = getBaseUrl();
    const musicFolder = 'threshold loops';
    const audioPath = `${baseUrl}/Music/${musicFolder}/s${currentSection}m${currentMeasure}.mp3`;
    console.log('Playing audio:', audioPath);
    const audio = new Audio(audioPath);
    
    audio.preload = 'auto';
    audio.volume = 1.0;
    
    isPlaying = true;
    
    const playPromise = audio.play();
    if (playPromise !== undefined) {
        playPromise.catch(e => {
            console.log('Audio play failed:', e, audioPath);
            isPlaying = false;
        });
    }
    
    audio.onended = () => {
        isPlaying = false;
        currentMeasure++;
        console.log('Audio ended, next will be: section', currentSection, 'measure', currentMeasure);
        if (currentMeasure > 4) {
            currentMeasure = 1;
            sectionPlayCount++;
            if (sectionPlayCount >= 2) {
                sectionPlayCount = 0;
                currentSection = currentSection === 1 ? 2 : 1;
                console.log('Switched to section', currentSection);
            }
        }
    };
}

document.addEventListener('DOMContentLoaded', function() {
    const logo = document.querySelector('img[src*="threshold artwork.png"]') || 
                 document.querySelector('img[src*="threshold%20artwork.png"]') ||
                 document.querySelector('img[alt="THRESHOLD"]');
    
    console.log('Threshold script loaded, logo found:', !!logo);
    if (logo) {
        console.log('Logo src:', logo.src);
        logo.addEventListener('click', playThresholdAudio);
        logo.addEventListener('touchend', function(e) {
            e.preventDefault();
            playThresholdAudio();
        });
        logo.style.cursor = 'pointer';
        logo.style.userSelect = 'none';
        logo.style.webkitUserSelect = 'none';
        logo.style.webkitTouchCallout = 'none';
    } else {
        console.log('Logo not found. Available images:', document.querySelectorAll('img'));
    }
});
