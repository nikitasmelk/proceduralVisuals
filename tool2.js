let scene, camera, renderer, sphere, analyser, audioContext, frequencyData, mouseX = 0, mouseY = 0;

document.getElementById('startButton').addEventListener('click', async () => {
    await initAudio();
    initThreeJS();
    document.getElementById('startButton').style.display = 'none'; // Hide the button
});

async function initAudio() {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        analyser.fftSize = 256;
        frequencyData = new Uint8Array(analyser.frequencyBinCount);
    } catch (error) {
        console.error('Error accessing microphone', error);
    }
}

function initThreeJS() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    let geometry = new THREE.SphereGeometry(1, 4, 5);
    let material = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true });
    sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);

    camera.position.z = 10;

    window.addEventListener('mousemove', onMouseMove, false);

    animate();
}

function animate() {
    requestAnimationFrame(animate);

    if (analyser) {
        analyser.getByteFrequencyData(frequencyData);
        let averageFrequency = getAverageFrequency(frequencyData);
        
        sphere.scale.set(1 + averageFrequency / 128, 1 + averageFrequency / 128, 1 + averageFrequency / 128);
        sphere.material.color.setHSL(averageFrequency / 256, 1, 0.5);

        // Chaotically change the camera's FOV
        camera.fov = 750 + averageFrequency * 0.01;
        camera.updateProjectionMatrix();
    }

    sphere.rotation.x += (mouseY - sphere.rotation.x) * 0.05;
    sphere.rotation.y += (mouseX - sphere.rotation.y) * 0.05;

    renderer.render(scene, camera);
}

function getAverageFrequency(dataArray) {
    let sum = dataArray.reduce((a, b) => a + b, 0);
    return sum / dataArray.length;
}

function onMouseMove(event) {
    mouseX = (event.clientX / window.innerWidth) * 2 - 1;
    mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
}
