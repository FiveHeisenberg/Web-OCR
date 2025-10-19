let inactivityTime = 0;
const TIMEOUT = 60000; // satuan ms/60 detik

function resetTimer() {
    inactivityTime = 0;
}

window.onload = () => {
    document.onmousemove = resetTimer;
    document.onkeypress = resetTimer;
    document.onscroll = resetTimer;
    document.onclick = resetTimer;

    // cek setiap 1 detik
    setInterval(() => {
        inactivityTime += 1000; // satuan ms/1 detik
        if (inactivityTime >= TIMEOUT) {
            location.reload(); // reload halaman, dan hapus file uploads
    }
    }, 1000);
};

// hapus file saat user menutup tab atau jendela
window.addEventListener("beforeunload", () => {
    fetch("/bersihkan", { method: "POST"});
});