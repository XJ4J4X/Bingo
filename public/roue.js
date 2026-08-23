// roue.js

const canvas = document.getElementById('wheel-canvas');
const ctx = canvas.getContext('2d');
const btnUpdate = document.getElementById('btn-update-wheel');
const btnSpin = document.getElementById('btn-spin');
const inputPhrases = document.getElementById('phrases-input');
const toggleGreenScreen = document.getElementById('green-screen-toggle');
const winnerOverlay = document.getElementById('winner-overlay');
const winnerText = document.getElementById('winner-text');
const btnCloseWinner = document.getElementById('btn-close-winner');

let phrases = [];
let currentRotation = 0;
let isSpinning = false;

// Vibrant palette
const colors = [
    '#6366f1', '#ec4899', '#14b8a6', '#f59e0b', 
    '#8b5cf6', '#ef4444', '#10b981', '#3b82f6',
    '#f43f5e', '#0ea5e9'
];

function init() {
    // Persistence
    const savedPhrases = localStorage.getItem('bingo_wheel_phrases');
    if (savedPhrases) {
        inputPhrases.value = savedPhrases;
    }

    parsePhrases();
    drawWheel();
    
    // Setup transition for CSS rotation
    canvas.style.transition = 'transform 5s cubic-bezier(0.2, 0.8, 0.3, 1)';
    
    btnUpdate.addEventListener('click', () => {
        localStorage.setItem('bingo_wheel_phrases', inputPhrases.value);
        parsePhrases();
        drawWheel();
        currentRotation = 0;
        canvas.style.transition = 'none';
        canvas.style.transform = `rotate(0deg)`;
    });
    
    btnSpin.addEventListener('click', spinWheel);
    
    btnCloseWinner.addEventListener('click', () => {
        winnerOverlay.classList.add('hidden');
    });
    
    toggleGreenScreen.addEventListener('change', (e) => {
        if (e.target.checked) {
            document.body.classList.add('green-screen');
        } else {
            document.body.classList.remove('green-screen');
        }
    });
    
    const btnToggleMenu = document.getElementById('btn-toggle-menu');
    const sidebar = document.getElementById('roue-sidebar');
    btnToggleMenu.addEventListener('click', () => {
        sidebar.classList.toggle('hidden');
    });
}

function parsePhrases() {
    const text = inputPhrases.value;
    phrases = text.split('\n')
                  .map(p => p.trim())
                  .filter(p => p.length > 0);
                  
    if (phrases.length === 0) {
        phrases = ["Ajoutez", "des", "phrases"];
    }
}

function drawWheel() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = centerX - 10;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (phrases.length === 0) return;
    
    const sliceAngle = (2 * Math.PI) / phrases.length;
    
    for (let i = 0; i < phrases.length; i++) {
        const startAngle = i * sliceAngle;
        const endAngle = (i + 1) * sliceAngle;
        
        // Draw slice
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        ctx.closePath();
        
        ctx.fillStyle = colors[i % colors.length];
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#ffffff';
        ctx.stroke();
        
        // Draw text
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(startAngle + sliceAngle / 2);
        ctx.textAlign = 'right';
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 20px Inter, sans-serif';
        ctx.shadowColor = 'rgba(0,0,0,0.5)';
        ctx.shadowBlur = 4;
        
        const text = phrases[i];
        // Truncate if too long
        let displayText = text.length > 25 ? text.substring(0, 22) + '...' : text;
        
        ctx.fillText(displayText, radius - 30, 8);
        ctx.restore();
    }
    
    // Draw center circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, 40, 0, 2 * Math.PI);
    ctx.fillStyle = '#0f172a';
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = '#ffffff';
    ctx.stroke();
}

function spinWheel() {
    if (isSpinning || phrases.length === 0) return;
    isSpinning = true;
    
    // Calculate new rotation: add 5 to 10 full spins plus a random offset
    const spins = Math.floor(Math.random() * 5) + 5; 
    const randomOffset = Math.random() * 360;
    
    currentRotation += (spins * 360) + randomOffset;
    
    canvas.style.transition = 'transform 5s cubic-bezier(0.2, 0.8, 0.3, 1)';
    canvas.style.transform = `rotate(${currentRotation}deg)`;
    
    // Wait for animation to finish
    setTimeout(() => {
        isSpinning = false;
        showWinner();
    }, 5000);
}

function showWinner() {
    // The pointer is at the top (270 degrees in canvas math, where 0 is right)
    // Slice i goes from i * (360/n) to (i+1) * (360/n)
    
    const sliceDegree = 360 / phrases.length;
    // Normalize current rotation to [0, 360)
    const normalizedRotation = currentRotation % 360;
    
    // Which degree of the original unrotated wheel is currently at the top (270)?
    // If we rotated by R, the point at the top was originally at 270 - R.
    let topDegree = (270 - normalizedRotation) % 360;
    if (topDegree < 0) topDegree += 360;
    
    const winnerIndex = Math.floor(topDegree / sliceDegree);
    const winner = phrases[winnerIndex];
    
    winnerText.textContent = winner;
    winnerOverlay.classList.remove('hidden');
    
    // Trigger confetti
    if (typeof confetti === 'function') {
        confetti({
            particleCount: 150,
            spread: 80,
            origin: { y: 0.6 },
            colors: ['#6366f1', '#ec4899', '#14b8a6']
        });
    }
}

// Initialize
init();
