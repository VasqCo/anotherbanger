(function() {
    var img = document.getElementById('matt-profile');
    var activated = false;
    var animationDone = false;
    var velocity = { x: 0, y: 0 };
    var gravity = 0.7;
    var bounce = 0.7;
    var friction = 0.85;
    var dragging = false;
    var offset = { x: 0, y: 0 };
    var lastMouse = { x: 0, y: 0 };
    var rafId;
    var rotation = 0;

    img.addEventListener('animationend', function() {
        animationDone = true;
        img.style.cursor = 'pointer';
    });

    var scoreCounter = document.createElement('div');
    scoreCounter.id = 'score-counter';
    scoreCounter.style.position = 'fixed';
    scoreCounter.style.top = '80px';
    scoreCounter.style.right = '10px';
    scoreCounter.style.color = '#fff';
    scoreCounter.style.fontSize = '24px';
    scoreCounter.style.display = 'none';
    scoreCounter.textContent = 'Score: 0';
    document.body.appendChild(scoreCounter);

    var hoop = document.createElement('img');
    hoop.id = 'basketball-hoop';
    hoop.src = '/basketballhoop.png';
    hoop.style.position = 'fixed';
    hoop.style.right = '-200px';
    hoop.style.top = '50%';
    hoop.style.transform = 'translateY(-50%)';
    hoop.style.width = '150px';
    hoop.style.height = 'auto';
    document.body.appendChild(hoop);

    var score = 0;
    var lastScoredTime = 0;
    var treasureFound = false;

    var treasure = document.createElement('div');
    treasure.id = 'hidden-treasure';
    treasure.style.position = 'absolute';
    treasure.style.width = '50px';
    treasure.style.height = '50px';
    treasure.style.backgroundColor = 'gold';
    treasure.style.borderRadius = '50%';
    treasure.style.opacity = '0';
    treasure.style.cursor = 'pointer';
    treasure.style.transition = 'opacity 0.3s ease';
    treasure.style.zIndex = '9998';
    treasure.style.display = 'none';
    treasure.innerHTML = '💰';
    treasure.style.fontSize = '30px';
    treasure.style.textAlign = 'center';
    treasure.style.lineHeight = '50px';
    function setRandomTreasurePosition() {
        var maxAttempts = 100;
        var attempts = 0;
        var validPosition = false;
        var treasureLeft, treasureTop;
        var pageWidth = Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);
        var pageHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
        while (!validPosition && attempts < maxAttempts) {
            treasureLeft = Math.random() * (pageWidth - 150) + 75;
            treasureTop = Math.random() * (pageHeight - 150) + 75;
            var conflicts = false;
            var conflictsWithScoreCounter = (
                treasureLeft + 50 > window.innerWidth - 200 && 
                treasureTop < window.scrollY + 130
            );
            var conflictsWithHoop = (
                treasureLeft + 50 > window.innerWidth - 210 && 
                treasureTop > window.scrollY + window.innerHeight * 0.4 && 
                treasureTop < window.scrollY + window.innerHeight * 0.6
            );
            var conflictsWithMattpng = (
                treasureLeft < 250 && treasureTop < 300
            );
            var tempDiv = document.createElement('div');
            tempDiv.style.position = 'absolute';
            tempDiv.style.left = treasureLeft + 'px';
            tempDiv.style.top = treasureTop + 'px';
            tempDiv.style.width = '50px';
            tempDiv.style.height = '50px';
            tempDiv.style.pointerEvents = 'none';
            tempDiv.style.visibility = 'hidden';
            document.body.appendChild(tempDiv);
            var tempRect = tempDiv.getBoundingClientRect();
            var elementsAtPosition = document.elementsFromPoint(
                tempRect.left + 25, 
                tempRect.top + 25
            );
            document.body.removeChild(tempDiv);
            for (var i = 0; i < elementsAtPosition.length; i++) {
                var elem = elementsAtPosition[i];
                var tagName = elem.tagName.toLowerCase();
                var className = elem.className || '';
                var id = elem.id || '';
                if (tagName === 'p' || tagName === 'h1' || tagName === 'h2' || tagName === 'h3' || 
                    tagName === 'h4' || tagName === 'h5' || tagName === 'h6' || tagName === 'span' ||
                    tagName === 'a' || tagName === 'audio' || tagName === 'figure' ||
                    className.includes('audio-demo') || className.includes('wave') ||
                    id === 'matt-profile' || id === 'matt-profile-placeholder') {
                    conflicts = true;
                    break;
                }
            }
            if (!conflictsWithScoreCounter && !conflictsWithHoop && !conflictsWithMattpng && !conflicts) {
                validPosition = true;
            }
            attempts++;
        }
        if (!validPosition) {
            treasureLeft = pageWidth * 0.7;
            treasureTop = pageHeight * 0.9;
        }
        treasure.style.position = 'absolute';
        treasure.style.left = treasureLeft + 'px';
        treasure.style.top = treasureTop + 'px';
    }
    setRandomTreasurePosition();
    document.body.appendChild(treasure);
    treasure.addEventListener('mouseenter', function() {
        if (!treasureFound) {
            treasure.style.opacity = '1.0';
        }
    });
    treasure.addEventListener('mouseleave', function() {
        if (!treasureFound) {
            treasure.style.opacity = '0';
        }
    });
    treasure.addEventListener('click', function() {
        if (!treasureFound) {
            treasureFound = true;
            score += 1000000;
            scoreCounter.textContent = 'Score: ' + score;
            var treasureMsg = document.createElement('div');
            treasureMsg.style.position = 'absolute';
            treasureMsg.style.left = treasure.style.left;
            treasureMsg.style.top = (parseInt(treasure.style.top) + 60) + 'px';
            treasureMsg.style.color = 'gold';
            treasureMsg.style.fontSize = '18px';
            treasureMsg.style.fontWeight = 'bold';
            treasureMsg.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
            treasureMsg.style.zIndex = '9999';
            treasureMsg.style.whiteSpace = 'nowrap';
            treasureMsg.textContent = 'NO MY MONEY! +1,000,000 points!';
            document.body.appendChild(treasureMsg);
            treasure.style.opacity = '0';
            setTimeout(function() {
                treasureMsg.style.opacity = '0';
                treasureMsg.style.transition = 'opacity 2s ease';
                setTimeout(function() {
                    document.body.removeChild(treasureMsg);
                }, 2000);
            }, 3000);
        }
    });
    img.addEventListener('click', function() {
        if (!animationDone || activated) return;
        activated = true;
        img.classList.remove('slide-left');
        img.style.transform = '';
        var rect = img.getBoundingClientRect();
        img.style.position = 'fixed';
        img.style.left = rect.left + 'px';
        img.style.top = rect.top + 'px';
        img.style.margin = '0';
        img.style.zIndex = 9999;
        img.style.cursor = 'grab';
        document.getElementById('matt-profile-placeholder').style.visibility = 'visible';
        scoreCounter.style.display = 'block';
        scoreCounter.style.visibility = 'visible';
        hoop.classList.add('slide-right');
        treasure.style.display = 'block';
        setRandomTreasurePosition();
        startPhysics();
    });
    function checkCollision() {
        var imgRect = img.getBoundingClientRect();
        var hoopRect = hoop.getBoundingClientRect();
        var currentTime = Date.now();
        if (
            imgRect.left < hoopRect.right &&
            imgRect.right > hoopRect.left &&
            imgRect.bottom > hoopRect.top &&
            imgRect.bottom < hoopRect.top + 30 &&
            velocity.y > 0 &&
            currentTime - lastScoredTime > 1000
        ) {
            score++;
            scoreCounter.textContent = 'Score: ' + score;
            lastScoredTime = currentTime;
        }
    }
    function startPhysics() {
        function step() {
            if (!dragging) {
                velocity.y += gravity;
                var left = parseFloat(img.style.left);
                var top = parseFloat(img.style.top);
                left += velocity.x;
                top += velocity.y;
                if (left < 0) { left = 0; velocity.x *= -bounce; }
                if (left + img.width > window.innerWidth) { left = window.innerWidth - img.width; velocity.x *= -bounce; }
                if (top < 0) { top = 0; velocity.y *= -bounce; }
                if (top + img.height > window.innerHeight) {
                    top = window.innerHeight - img.height;
                    velocity.y *= -bounce;
                    velocity.x *= friction;
                    if (Math.abs(velocity.y) < 1) velocity.y = 0;
                }
                rotation += velocity.x;
                img.style.transform = 'rotate(' + rotation + 'deg)';
                img.style.left = left + 'px';
                img.style.top = top + 'px';
                checkCollision();
            }
            rafId = requestAnimationFrame(step);
        }
        rafId = requestAnimationFrame(step);
    }
    img.addEventListener('mousedown', function(e) {
        if (!activated) return;
        dragging = true;
        img.style.cursor = 'grabbing';
        window.getSelection().removeAllRanges();
        offset.x = e.clientX - parseFloat(img.style.left);
        offset.y = e.clientY - parseFloat(img.style.top);
        lastMouse.x = e.clientX;
        lastMouse.y = e.clientY;
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
    img.addEventListener('dragstart', function(e) { e.preventDefault(); });
    function onMove(e) {
        if (!dragging) return;
        var newLeft = e.clientX - offset.x;
        var newTop = e.clientY - offset.y;
        velocity.x = e.clientX - lastMouse.x;
        velocity.y = e.clientY - lastMouse.y;
        img.style.left = newLeft + 'px';
        img.style.top = newTop + 'px';
        lastMouse.x = e.clientX;
        lastMouse.y = e.clientY;
        if (!dragging) {
            rotation += velocity.x;
            img.style.transform = 'rotate(' + rotation + 'deg)';
        }
    }
    function onUp(e) {
        if (e.button !== 0) return; 
        dragging = false;
        img.style.cursor = 'grab';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
    }
})();
