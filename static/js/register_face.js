import axios from 'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js';
axios.defaults.withCredentials = true;

// Register Face
const registerFaceForm = document.getElementById('register-face-form');
const registerMessageEl = document.getElementById('register-message');
const faceImageEl = document.getElementById('face-image');
const registerBtn = document.getElementById('registerBtn');

registerFaceForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  registerBtn.disabled = true;
  registerMessageEl.textContent = 'Registering...';
  
  const firstNameInput = document.getElementById('first-name');
  const lastNameInput = document.getElementById('last-name');
  const firstName = firstNameInput.value;
  const lastName = lastNameInput.value;

  // Clear previous messages
  document.getElementById('first-name-error').textContent = '';
  document.getElementById('last-name-error').textContent = '';
  faceImageEl.style.display = 'none';
  
try {
  // Validate first name
  if (!firstNameInput.checkValidity()) {
    document.getElementById('first-name-error').textContent = 'Invalid first name. It must be 3-20 characters long and contain only letters and spaces.';
    return;
  }
  // Validate last name
  if (!lastNameInput.checkValidity()) {
    document.getElementById('last-name-error').textContent = 'Invalid last name. It must be 3-20 characters long and contain only letters and spaces.';
    return;
  }
  
    const res = await axios.post('/register_face', { first_name: firstName, last_name: lastName });
    if (res.data.status === 'success') {
      registerMessageEl.textContent = res.data.message;
      faceImageEl.src = `data:image/jpeg;base64,${res.data.image}`;
      faceImageEl.style.display = 'block';
      fetchFaces();  // Refresh the face list after registration
    }} catch (error) {
      if (error.response?.status === 401) {
        registerMessageEl.innerHTML = "Unauthorized access. You will be redirected to the login page in 5 seconds. <a href='/login.html'>Press here to Go now</a>";
        setTimeout(() => { window.location.href = '/login.html'; // Redirect to login to unauthurized users
        }, 5000);
    } else if (error.response) {
      console.error('Error registering face in register_face.js:', error);
      registerMessageEl.textContent = error.response?.data?.detail || 'Error registering face, Please try again';
    } else if (error.request) {
      console.error('No response received from server:', error.request);
      registerMessageEl.textContent = 'Network error: Unable to reach server, Please try again';
    } else {
      console.error('Unexpected error registering face in register_face.js:', error);
      registerMessageEl.textContent = 'Unexpected error occurred, Please try again';
    }} finally {
    registerBtn.disabled = false;
  }
  });

// Delete Face
const deleteFaceForm = document.getElementById('delete-face-form');
const deleteMessageEl = document.getElementById('delete-message');
const deleteBtn = document.getElementById('deleteBtn');

deleteFaceForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  deleteBtn.disabled = true;
  const faceIdInput = document.getElementById('delete-face-id');
  const faceId = faceIdInput.value;

  // Clear previous messages
  deleteMessageEl.textContent = '';
  document.getElementById('face-id-error').textContent = '';

try {
// Validate face ID
if (!faceIdInput.checkValidity()) {
  document.getElementById('face-id-error').textContent = 'Invalid Face ID. It must be a positive integer.';
  return;
}
    const res = await axios.delete(`/delete_face/${faceId}`);
    if (res) {
    deleteMessageEl.textContent = res.data.message;
    faceIdInput.value = '';
    fetchFaces(); // Refresh the face list after deletion
    }
  } catch (error) {
    if (error.response?.status === 401) {
      deleteMessageEl.innerHTML = "Unauthorized access. You will be redirected to the login page in 5 seconds. <a href='/login.html'>Press here to Go now</a>";
      setTimeout(() => { window.location.href = '/login.html'; // Redirect to login to unauthurized users
      }, 5000); 
  } else if (error.response) {
    console.error('Error deleting face in register_face.js:', error);
    deleteMessageEl.textContent = error.response?.data?.detail || 'Error deleting face, Please try again';
  } else if (error.request) {
    console.error('No response received from server:', error.request);
    deleteMessageEl.textContent = 'Network error: Unable to reach server, Please try again';
  } else {
    console.error('Unexpected error deleting face in register_face.js:', error);
    deleteMessageEl.textContent = error.response?.data?.detail || 'Unexpected error deleting face, Please try again';
  }} finally {
    deleteBtn.disabled = false;
  }
});

// Refresh Live Feed
const refreshLiveFeedBtn = document.getElementById('refresh-live-feed');
const liveFeedImg = document.getElementById('live-feed');
const liveFresh = document.getElementById('livefresh');
refreshLiveFeedBtn.addEventListener('click', () => {
  refreshLiveFeedBtn.disabled = true; // defend the server from abuse
  // Append a timestamp to bypass any caching freeze
  liveFresh.textContent = "Rfreshing feed, please wait..."
  liveFeedImg.src = `/register_video_feed?timestamp=${new Date().getTime()}`;
  setTimeout(() => {
    refreshLiveFeedBtn.disabled = false;
  }, 1000);
  liveFresh.textContent = ""
});

// List Faces
const refreshFacesBtn = document.getElementById('refresh-faces');
const facesListEl = document.getElementById('faces-list');

async function fetchFaces() {
  refreshFacesBtn.disabled = true;
  facesListEl.innerHTML = '<li>Loading...</li>';
  try {
    const res = await axios.get('/list_faces');
    if (res.data.faces && res.data.faces.length) {
      const fragment = document.createDocumentFragment();
      res.data.faces.forEach(face => {
        const li = document.createElement('li');
        li.textContent = `ID: ${face.id}, Name: ${face.first_name} ${face.last_name}, Created: ${face.created_at}`; //If raw timestamp -> Created: ${new Date(face.created_at).toLocaleString()}`;
        fragment.appendChild(li);
      });
      facesListEl.appendChild(fragment);
    } else {
      facesListEl.innerHTML = '<li>No faces registered</li>';
    }
  } catch (error) {
    if (error.response?.status === 401) {
      facesListEl.innerHTML = "<li>Unauthorized access. You will be redirected to the login page in 5 seconds. <a href='/login.html'>Press here to Go now</a></li>";
      setTimeout(() => { window.location.href = '/login.html'; // Redirect to login to unauthurized users
      }, 5000);
  } else if (error.response) {
    console.error('Error fetching faces list in register_face.js:', error);
    facesListEl.innerHTML = error.response?.data?.detail || 'Unexpected error fetching faces, please refresh. If it persists, report to support and try again.';
  } else if (error.request) {
    console.error('No response received from server:', error.request);
    facesListEl.innerHTML = "<li>Network error: Unable to reach the server. Please check your connection and try again.</li>";
  } else {
    console.error('Error setting up request:', error);
    facesListEl.innerHTML = "<li>An unexpected error occurred. Please try again later.</li>";
  }
    } finally {
    refreshFacesBtn.disabled = false;
  }
}
refreshFacesBtn.addEventListener('click', fetchFaces);
fetchFaces(); // Initial fetch on page load