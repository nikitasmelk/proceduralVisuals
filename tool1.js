const startButton = document.getElementById('startButton');
const canvas = document.getElementById('roseCanvas');
canvas.style.border = 'none'; // Remove the border
const ctx = canvas.getContext('2d');
const centerX = canvas.width / 2;
const centerY = canvas.height / 2;
const numPetals = 10;
let audioContext;
let analyser;
let volume = 0;
let lastUpdateTime = 0;

startButton.addEventListener('click', () => {
    // Start the AudioContext on user gesture
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048; // Increase fftSize for better pitch detection

    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        .then(function(stream) {
            audioContext.createMediaStreamSource(stream).connect(analyser);
            lastUpdateTime = performance.now();
            drawAnimation(); // Start drawing after user gesture
        });

    startButton.style.display = 'none'; // Hide the button after starting
});

function drawPetal(x, y, angle, petalLength, petalWidth, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.ellipse(0, 0, petalWidth, petalLength, 0, 0, 2 * Math.PI);
  ctx.strokeStyle = color; // Use the color based on pitch
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.restore();
}

function updateAudioData() {
    let bufferLength = analyser.frequencyBinCount;
    let dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);

    let sum = dataArray.reduce((a, b) => a + b, 0);
    volume = sum / dataArray.length / 128.0; // Normalized volume (0-1)
}

function getPitchColor(dataArray) {
    let maxIndex = dataArray.indexOf(Math.max(...dataArray));
    let hue = (maxIndex / dataArray.length) * 360; // Map to hue for color
    return `hsl(${hue}, 100%, 50%)`; // Return HSL color based on pitch
}

function drawCenterObject(color) {
    ctx.beginPath();
    ctx.arc(centerX, centerY, 5 * (1 + volume * 3), 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
}

function drawRose(color) { // Add color parameter
  for (let i = 0; i < numPetals; i++) {
      let angle = (i / numPetals) * 20 * Math.PI * Math.random();
      let radius = 5 + Math.random() * 300 * volume;
      let petalLength = 30 + Math.random() * 300 * volume;
      let petalWidth = 15 + Math.random() * 300 * volume;
      let x = centerX + Math.cos(angle) * radius;
      let y = centerY + Math.sin(angle) * radius;
      drawPetal(x, y, angle, petalLength, petalWidth, color); // Pass the color to drawPetal
  }
}

function drawAnimation() {
  let currentTime = performance.now();
  let timeDiff = currentTime - lastUpdateTime;
  lastUpdateTime = currentTime;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  updateAudioData();

  let bufferLength = analyser.frequencyBinCount;
  let dataArray = new Uint8Array(bufferLength);
  analyser.getByteTimeDomainData(dataArray);
  let color = getPitchColor(dataArray);

  drawRose(color); // Pass the color to drawRose
  drawCenterObject(color);

  let delay = 10 - (volume * 900);
  setTimeout(() => requestAnimationFrame(drawAnimation), delay);
}

// The drawing starts when the user clicks the start button.
