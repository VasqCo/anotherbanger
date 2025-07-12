let currentSection = 1;
let currentMeasure = 1;
let sectionPlayCount = 0;
let isPlaying = false;

function playThresholdAudio() {
    if (isPlaying) return;
    
    const logo = document.querySelector('img[src="/threshold artwork.png"]');
    const audioPath = `/Music/threshold loops/s${currentSection}m${currentMeasure}.mp3`;
    const audio = new Audio(audioPath);
    
    isPlaying = true;
    
    audio.play().catch(e => console.log('Audio play failed:', e));
    
    audio.onended = () => {
        isPlaying = false;
        
        currentMeasure++;
        
        if (currentMeasure > 4) {
            currentMeasure = 1;
            sectionPlayCount++;
            
            if (sectionPlayCount >= 2) {
                sectionPlayCount = 0;
                currentSection = currentSection === 1 ? 2 : 1;
            }
        }
    };
}

document.addEventListener('DOMContentLoaded', function() {
    const logo = document.querySelector('img[src="/threshold artwork.png"]');
    if (logo) {
        logo.addEventListener('click', playThresholdAudio);
    }
});
