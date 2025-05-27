import axios from 'https://esm.sh/axios';
axios.defaults.withCredentials = true;

// CONFIG
// Function to handle error messages and site redirection,
//  not getting body content, due to using only the HEAD to get status
function handleInitialError(error) {
    spinner.style.display = 'none'; // Hide the spinner
    //refreshBtn.disabled = false; // NOT ENABLING THE BUTTON --- because i want to force the user to refresh the page to start new server connection
    refreshBtn.style.display = 'none'; // Hide the button
    liveFeedImg.style.display = 'none'; // Hide the image
    statusMessage.textContent = ''; // Clear the status message
    console.error('Error in livefeed.js:', error); // Log the error to the console

    if (error.response) { const status = error.response?.status;
        if (status === 401) {alert("Unauthorized. Redirecting to login..."); window.location.href = '/Login.html';}
        else if (status === 403) {alert("You were disabled from the system. hash it out?"); window.location.href = '/Login.html';} 
        else if (status === 404) {statusMessage.textContent = 'Live feed not available. Click Refresh page to try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)';}
        else if (status === 500) {statusMessage.textContent = 'Server error. Try again later or contact support. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)';}
        else {statusMessage.textContent = `Error: ${status}. Click Refresh page to try again if persists tell support. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)`;}} 
    else {statusMessage.textContent = 'Network error. Click Refresh page to try again. (press CTRL-Shift-R for hard refresh if regular refresh doesnt work)';} } // Handle network errors

// ------------------------------------------------------------------
// ------------------------------------------------------------------
// DOM elements
const liveFeedImg = document.getElementById('live-feed');
const refreshBtn = document.getElementById('refresh-feed');
const statusMessage = document.getElementById('status-message');
const spinner = document.querySelector('.spinner');

// Function to update the live feed
async function updateLiveFeed() {
    try {
        spinner.style.display = 'block'; // Show the spinner until image loads
        statusMessage.textContent = 'Loading live feed...'; // Update status message
        // Add a timestamp to prevent caching issues
        const timestamp = new Date().getTime();
        const url = `/video_feed?timestamp=${timestamp}`;
        const response = await axios.head(url); // Check stream availability with Axios
        if (response.status === 200) {
        console.log("200, Stream available, displaying livestream");
        refreshBtn.disabled = true;
        spinner.style.display = 'none'; // Hide the spinner
        statusMessage.textContent = ''; // Clear the status message
        liveFeedImg.style.display = 'block'; // Show the image
        refreshBtn.style.display = 'inline-block';
        setTimeout( () => {refreshBtn.disabled = false;}, 2000); }}
    catch (error) {handleInitialError(error);} }

// When the stream fails mid-feed
liveFeedImg.onerror = (e) => {
    console.error("Image load error:", e);
    refreshBtn.style.display = 'none';
    liveFeedImg.style.display = 'none';
    spinner.style.display = 'block';
    statusMessage.textContent = `Live feed lost. Retrying in 5 seconds...`;
    setTimeout(() =>{window.location.reload(true);}, 5000);} // reload page after 5 seconds, cant reload streaming request with timestamp

// Event listeners to actiavte when even happens ----------------------------
refreshBtn.addEventListener('click', () =>{window.location.reload(true);});
window.addEventListener('load', updateLiveFeed);