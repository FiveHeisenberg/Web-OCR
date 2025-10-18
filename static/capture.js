const video = document.getElementById('video');
const snapBtn = document.getElementById('snap');
const accessBtn = document.getElementById('accessCamera');
const canvas = document.getElementById('canvas');
const imageInput = document.getElementById('image_data');

accessBtn.addEventListener('click', () => {
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        
      video.srcObject = stream;
      video.style.display = 'block';
      snapBtn.style.display = 'block';
      // sembunyikan tombol akses kamera
      accessBtn.style.display = 'none'; 
    })
    .catch(err => {
      console.error('Error akses webcam', err);
      alert('Tidak bisa mengakses webcam');
    });
});

snapBtn.addEventListener('click', () => {
  const ctx = canvas.getContext('2d');
  canvas.style.display = 'block';
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataURL = canvas.toDataURL('image/png');
  imageInput.value = dataURL;
  alert('Foto diambil. Tekan "Kirim Hasil Foto untuk OCR".');
});
