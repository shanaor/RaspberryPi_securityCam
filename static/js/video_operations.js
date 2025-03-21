import axios from 'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js';
axios.defaults.withCredentials = true;

const listEl = document.getElementById('video-list');
const refreshBtn = document.getElementById('refresh');

async function fetchVideos() {
  try {
    const { data: videos } = await axios.get('/videos_list/');
    listEl.innerHTML = '';
    const fragment = document.createDocumentFragment();
    videos.forEach(video => {
      const li = document.createElement('li');
      li.textContent = video;
      
      // Download link
      const downloadLink = document.createElement('a');
      downloadLink.href = `/videos/download/${video}`;
      downloadLink.textContent = 'Download';
      downloadLink.style.marginLeft = '10px';
      
      // Delete button (admin only)
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = 'Delete';
      deleteBtn.style.marginLeft = '10px';
      deleteBtn.onclick = async () => {
        try {
          await axios.delete(`/videos/delete/${video}`);
          alert(`Deleted ${video}`);
          fetchVideos();
        } catch (err) {
          alert('Delete failed');
        }
      };
      
      li.append(downloadLink, deleteBtn);
      fragment.appendChild(li);
    });
    listEl.appendChild(fragment);
  } catch (err) {
    listEl.innerHTML = '<li>Error loading videos</li>';
  }
}

refreshBtn.addEventListener('click', fetchVideos);
fetchVideos();
