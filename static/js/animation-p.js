const container = document.getElementById("alchicken-intro");

// Scene
const scene = new THREE.Scene();

// Camera
const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.z = 5;

// Renderer (attached to container, NOT body)
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

// Light
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(2, 2, 5);
scene.add(light);

// Load Logo
const loader = new THREE.TextureLoader();
const texture = loader.load("/static/images/logo.png");
// Plane
const geometry = new THREE.PlaneGeometry(4, 2);
const material = new THREE.MeshBasicMaterial({
    map: texture,
    transparent: true
});

const logo = new THREE.Mesh(geometry, material);
scene.add(logo);

// Greeting
const text = document.getElementById("alchicken-text");

function getGreeting() {
    const hour = new Date().getHours();

    if (hour >= 5 && hour < 12) {
        return "Morning Quack 🐔";
    } else if (hour >= 12 && hour < 18) {
        return "Good Afternoon Quack 🐔";
    } else {
        return "Good Night Quack 🐔";
    }
}

text.innerHTML = getGreeting();

// Show text
setTimeout(() => {
    text.style.opacity = 1;
}, 500);

// Animation
let t = 0;

function animate() {
    requestAnimationFrame(animate);

    t += 0.05;

    logo.position.y = Math.sin(t * 2) * 0.3;
    logo.rotation.z = Math.sin(t * 3) * 0.1;

    const scale = 1 + Math.sin(t * 4) * 0.05;
    logo.scale.set(scale, scale, scale);

    renderer.render(scene, camera);
}

animate();

// Remove after 5s
setTimeout(() => {
    container.style.transition = "opacity 1s ease";
    container.style.opacity = 0;

    setTimeout(() => {
        container.remove(); // completely removes from DOM
    }, 1000);

}, 2000);

// Resize fix
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});