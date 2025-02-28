import axios from 'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js';

// Register Face
const registerFaceForm = document.getElementById('register-face-form');
const registerMessageEl = document.getElementById('register-message');
const faceImageEl = document.getElementById('face-image');

registerFaceForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const firstName = document.getElementById('first-name').value;
  const lastName = document.getElementById('last-name').value;
  try {
    const res = await axios.post('/register_face', { first_name: firstName, last_name: lastName });
    if (res.data.status === 'success') {
      registerMessageEl.textContent = res.data.message;
      faceImageEl.src = `data:image/jpeg;base64,${res.data.image}`;
      faceImageEl.style.display = 'block';
    } else {
      registerMessageEl.textContent = res.data.message;
      faceImageEl.style.display = 'none';
    }
  } catch (error) {
    registerMessageEl.textContent = error.response?.data?.detail || 'Error registering face';
    faceImageEl.style.display = 'none';
  }
});

// Delete Face
const deleteFaceForm = document.getElementById('delete-face-form');
const deleteMessageEl = document.getElementById('delete-message');

deleteFaceForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const faceId = document.getElementById('delete-face-id').value;
  try {
    const res = await axios.delete(`/delete_face/${faceId}`);
    deleteMessageEl.textContent = res.data.message;
    fetchFaces();
  } catch (error) {
    deleteMessageEl.textContent = error.response?.data?.detail || 'Error deleting face';
  }
});

// Refresh Live Feed
const refreshLiveFeedBtn = document.getElementById('refresh-live-feed');
const liveFeedImg = document.getElementById('live-feed');
refreshLiveFeedBtn.addEventListener('click', () => {
  // Append a timestamp to bypass any caching freeze
  liveFeedImg.src = `/register_video_feed?timestamp=${new Date().getTime()}`;
});

// List Faces
const refreshFacesBtn = document.getElementById('refresh-faces');
const facesListEl = document.getElementById('faces-list');

async function fetchFaces() {
  try {
    const res = await axios.get('/list_faces');
    facesListEl.innerHTML = '';
    if (res.data.faces && res.data.faces.length) {
      res.data.faces.forEach(face => {
        const li = document.createElement('li');
        li.textContent = `ID: ${face.id}, Name: ${face.first_name} ${face.last_name}, Created: ${face.created_at}`;
        facesListEl.appendChild(li);
      });
    } else {
      facesListEl.innerHTML = '<li>No faces registered</li>';
    }
  } catch (error) {
    facesListEl.innerHTML = '<li>Error fetching faces</li>';
  }
}
refreshFacesBtn.addEventListener('click', fetchFaces);
fetchFaces();
