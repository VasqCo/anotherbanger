function shakeElement(element, options = {}) {
    const amplitude = options.amplitude || 8;
    const frequency = options.frequency || 40;
    const duration = options.duration || 600;
    const axis = options.axis || 'both';
    if (!element) return;
    let start = null;
    let animationFrame;
    const originalStyle = element.style.transform || '';
    function animateShake(timestamp) {
        if (!start) start = timestamp;
        const elapsed = timestamp - start;
        if (elapsed < duration) {
            const angle = (elapsed / 1000) * frequency * 2 * Math.PI;
            let x = 0, y = 0;
            if (axis === 'x' || axis === 'both') x = Math.sin(angle) * amplitude;
            if (axis === 'y' || axis === 'both') y = Math.cos(angle) * amplitude;
            element.style.transform = `${originalStyle} translate(${x}px, ${y}px)`;
            animationFrame = requestAnimationFrame(animateShake);
        } else {
            element.style.transform = originalStyle;
            cancelAnimationFrame(animationFrame);
        }
    }
    animationFrame = requestAnimationFrame(animateShake);
}

document.addEventListener('DOMContentLoaded', function() {
    var shakeSpans = document.querySelectorAll('span.shake');
    shakeSpans.forEach(function(span) {
        var text = span.textContent;
        span.textContent = '';
        var word = '';
        var nodes = [];
        function flushWord() {
            if (word.length > 0) {
                var wordSpan = document.createElement('span');
                wordSpan.style.display = 'inline-block';
                for (let i = 0; i < word.length; i++) {
                    var letterSpan = document.createElement('span');
                    letterSpan.textContent = word[i];
                    letterSpan.style.display = 'inline-block';
                    letterSpan.style.willChange = 'transform';
                    wordSpan.appendChild(letterSpan);
                }
                span.appendChild(wordSpan);
                nodes.push(wordSpan);
                word = '';
            }
        }
        for (let i = 0; i < text.length; i++) {
            if (text[i] === ' ') {
                flushWord();
                var space = document.createTextNode(' ');
                span.appendChild(space);
            } else {
                word += text[i];
            }
        }
        flushWord();
        let amplitude = 1.1;
        function animate() {
            nodes.forEach(function(wordSpan) {
                for (let i = 0; i < wordSpan.childNodes.length; i++) {
                    let letterSpan = wordSpan.childNodes[i];
                    let x = (Math.random() - 0.5) * 2 * amplitude;
                    let y = (Math.random() - 0.5) * 2 * amplitude;
                    letterSpan.style.transform = `translate(${x}px, ${y}px)`;
                }
            });
            requestAnimationFrame(animate);
        }
        animate();
    });
});
