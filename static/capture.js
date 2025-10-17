// akses webcam dan ambil foto
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const snapBtn = document.getElementById('snap');
const imageInput = document.getElementById('image_data');


navigator.mediaDevices.getUserMedia({ video: true })
.then(stream => { video.srcObject = stream; })
.catch(err => { console.error('Error akses webcam', err); alert('Tidak bisa mengakses webcam'); });


snapBtn.addEventListener('click', () => {
const ctx = canvas.getContext('2d');
ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
const dataURL = canvas.toDataURL('image/png');
imageInput.value = dataURL;
alert('Foto diambil. Tekan \"Kirim Hasil Foto untuk OCR\".');
});