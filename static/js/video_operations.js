import axios from 'https://esm.sh/axios';
axios.defaults.withCredentials = true;

// CONFIG
// Function to handle error messages and site redirection
function handleError_textcontext(error_var,htmltext,failed_action,del_flag) {    
   // check if there is an error response from the server
    const status = error_var.response?.status;
    const detail = error_var.response?.data?.detail;
    console.error("error in video_operations.js:",error_var);

  if (del_flag == true){
    if (error_var.response) { // check if there is an error response from the server
        if (status === 401) {alert(`${detail}`); window.location.href = '/Login.html';} // Redirect to login to unauthurized users  
        else if (status === 403) {alert(`${detail}`); window.location.href = '/Livefeed.html';} // Redirect to livefeed to unauthurized action, to penalize bad behavior
        else if (status === 404) {alert(`${detail}`);} // Re-enable button after 404 error
        else if (status === 500) {alert(`${detail}`);}
        else {alert(`Unexpected Error ${failed_action}. REFRESH page Please try again. if persists, contact support`);}
    // Setup error or other client-side issue
  } else if (error_var.request) {alert('Network Error: Could not reach server. REFRESH page and try again');}
    else {alert(`Client Error: ${error_var.message}. REFRESH page and try again`);}}; // Network connection error
  
  if (del_flag == false){
    if (error_var.response) {
        if      (status === 400) {htmltext.textContent = `${detail}`;}
        else if (status === 401) {alert(`${detail}`); window.location.href = '/Login.html';} // Redirect to login to unauthurized users
        else if (status === 403) {alert(`${detail}`); window.location.href = '/Livefeed.html';} // Redirect to livefeed to unauthurized action, to penalize bad behavior
        else if (status === 404) {htmltext.textContent = `${detail}`;} // Re-enable button after 404 error
        else if (status === 409) {htmltext.textContent = `${detail}`;}
        else if (status === 500) {htmltext.textContent = `${detail}`;}
        else {htmltext.textContent = `Failed ${failed_action}. Please REFRESH page and try again.`;}
  // Setup error or other client-side issue
  } else if (error_var.request) {htmltext.textContent = 'Network Error: Could not reach server. REFRESH page and try again';}
    else {htmltext.textContent = `Client Error: ${error_var.message}. REFRESH page and try again`;}};}; // Network connection error
// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------

const listEl = document.getElementById('video-list');
const refreshBtn = document.getElementById('refresh');
const notifier = document.getElementById("notifier");

async function fetchVideos() {
    notifier.textContent = 'Loading videos...';
    refreshBtn.disabled = true;
  try {
      const { data: videos } = await axios.get('/videos_list/');
      const fragment = document.createDocumentFragment();
      
      if (videos.length === 0) {
          listEl.textContent = 'No videos available.';
          refreshBtn.disabled = false; // Re-enable button if no videos
          return;}

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
        deleteBtn.textContent = 'Delete (Admin only)';
        deleteBtn.style.backgroundColor = 'red';
        deleteBtn.style.color = 'white';
        deleteBtn.style.marginLeft = '10px';
        deleteBtn.onclick = async () => {
        const videoName = video; // Get the video name for the message
        
          if (confirm(`Are you sure you want to delete the video "${videoName}"? This action cannot be undone.`)) {
              deleteBtn.disabled = true; // disable button, prevent server harrasment and force the user to Refresh the page
              try {
                await axios.delete(`/videos/delete/${videoName}`);
                alert(`Deleted ${videoName}`);
                deleteBtn.disabled = false;
                listEl.textContent = ''; // Clear the list
                fetchVideos();
            } catch (error_delete) {
                console.error('Error deleting video:', error_delete);
                const del_flag = true;
                const failed_action = `Deleting video ${videoName}`;
                handleError_textcontext(error_delete,null,failed_action,del_flag);}} 
          else {alert(`Deletion of ${videoName} was cancelled.`); deleteBtn.disabled = false;}};
        
        li.append(downloadLink, deleteBtn);
        fragment.appendChild(li); 
      });
      listEl.appendChild(fragment);
      notifier.textContent = '';
      refreshBtn.disabled = false; // Re-enable button after successful fetch
  } catch (error_list) { // Handle errors for downloading and listing videos (so 2 sections of video_operations.py)
      console.error('Error fetching videos:', error_list);
      const failed_action = "loading video list";
      const del_flag = false;
      handleError_textcontext(error_list,listEl,failed_action,del_flag);}
};
refreshBtn.addEventListener('click', fetchVideos);
fetchVideos();