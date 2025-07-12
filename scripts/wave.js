document.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll('.wave').forEach(function(el) {
    const text = el.textContent;
    el.innerHTML = '';
    for (let i = 0; i < text.length; i++) {
      const span = document.createElement('span');
      if (text[i] === ' ') {
        span.innerHTML = '&nbsp;';
        span.style.width = '1ch';
        span.style.display = 'inline-block';
      } else {
        span.textContent = text[i];
        span.style.animation = `wave 3s infinite ease-in-out`;
        span.style.animationDelay = (i * 0.08) + 's';
        span.style.display = 'inline-block';
      }
      el.appendChild(span);
    }
  });
});
