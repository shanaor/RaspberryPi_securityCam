import axios from 'https://esm.sh/axios';
axios.defaults.withCredentials = true;

// ---------- CONFIG --------------
// --- Error Handler ---
function handleError_textcontext(error_var,htmltext,failed_action,button,consolemsg) {    
  console.error(`error in register_face.js ${consolemsg} `,error_var);
  
  if (error_var.response) { // check if there is an error response from the server
    const status = error_var.response?.status;
    const detail = error_var.response?.data?.detail || 'Unknown error';

    if      (status === 400) {htmltext.textContent = `${detail}`; button.disabled = false;} // Re-enable button after 400 error
    else if (status === 401) {alert(`${detail}`); window.location.href = '/Login.html';} // Redirect to login to unauthurized users
    else if (status === 403) {alert(`${detail}`); window.location.href = '/Livefeed.html';} // Redirect to livefeed to unauthurized action, to penalize bad behavior
    else if (status === 404) {htmltext.textContent = `${detail}`; button.disabled = false;} // Re-enable button after 404 error 
    else if (status === 409) {htmltext.textContent = `${detail}`; button.disabled = false;}
    else if (status === 500) {htmltext.textContent = `${detail}`; button.disabled = true;}
    else if (error_var.message){htmltext.textContent = `${error_var.message}`; button.disabled = false;} // Catch the custom "throw new error"
    else {htmltext.textContent = `Failed ${failed_action}. Please REFRESH page and try again.`; button.disabled = true;} // Handle other status codes
  // Setup error or other client-side issue
  } else if (error_var.request) {htmltext.textContent = 'Network Error: Could not reach server. REFRESH page and try again'; button.disabled = true;}
    else {htmltext.textContent = `Client Error: ${error_var.message}. REFRESH page and try again`; button.disabled = true;}} // Network connection error

// ----------------------------------------------------------------------------------------------------------------------------------------------------------
// --- Validation Function ---
function validate_NameInputs(firstNameElement,lastNameElement,firstNameError,lastNameError,button) {
    // Clear previous messages
    firstNameError.textContent = ''; lastNameError.textContent = '';
  // Validate first name and last name
      if (!firstNameElement.checkValidity()) {firstNameError.textContent = 'Invalid first name. It must be 3-20 characters long and contain only letters and spaces.'; button.disabled = false;
        return false; } // Indicating failure
      if (!lastNameElement.checkValidity()) {lastNameError.textContent = 'Invalid last name. It must be 3-20 characters long and contain only letters and spaces.'; button.disabled = false;
        return false; } // Indicating failure
    return true;} // If both validations, pass true Indicating succes
function validate_poll_configs(POLLING_INTERVAL_MS, MAX_CAPTURE_ATTEMPTS) {
  // Validate inputs
  if (isNaN(POLLING_INTERVAL_MS) || isNaN(MAX_CAPTURE_ATTEMPTS)) {alert("Please enter Only numbers for polling interval and max attempts."); return false;} // Exit if invalid inputs
  if (POLLING_INTERVAL_MS < 1000 || POLLING_INTERVAL_MS > 10000) {alert("Polling interval loop must be at least 1 second(1000) to 10 seconds(10000)."); return false;} // Exit if invalid inputs
  if (MAX_CAPTURE_ATTEMPTS < 1 || MAX_CAPTURE_ATTEMPTS > 100 ) {alert("Max attempts must be at least 1 and maximum 100."); return false;} // Exit if invalid inputs
  return true;} // Indicating success
// ----------------------------------------------------------------------------------------------------------------------------------------------------------
// ----------------------------------------------------------------------------------------------------------------------------------------------------------
// ----------------------------------------------------------------------------------------------------------------------------------------------------------

// --- State Variables ---
let isCapturing = false;
let pollingIntervalId = null;
let captureAttemptCount = 0;
let capturedEncoding = null; // Store the received encoding list

// --- Face Capture Logic -------------
const startCaptureBtn = document.getElementById('start-capture-btn');
const cancelCaptureBtn = document.getElementById('cancel-capture-btn');

const facePreviewImg = document.getElementById('face-preview-img');
const captureStatusMessage = document.getElementById('capture-status-message');
const captureSpinner = document.getElementById('capture-spinner');


function stopCaptureProcess(reason, data = null,MAX_CAPTURE_ATTEMPTS) {
  console.log(`Stopping capture process. Reason: ${reason}`);
  isCapturing = false;
  
  if (pollingIntervalId) {clearInterval(pollingIntervalId); pollingIntervalId = null;}

  startCaptureBtn.style.display = 'inline-block'; startCaptureBtn.disabled = false;
  cancelCaptureBtn.style.display = 'none'; captureSpinner.style.display = 'none'; facePreviewImg.style.display = 'none'; registerDetailsForm.style.display = 'none'; // Hide form, preview image, spinner and cancel button

  switch (reason) {
    case "Success":
        captureStatusMessage.textContent = data?.message || 'Face detected. If you want to register the Face to memory, enter the details below.';
        facePreviewImg.src = `data:image/jpeg;base64,${data?.image}`; facePreviewImg.style.display = 'block'; // show the image
        capturedEncoding = data?.encoding; // Store the encoding (as a list)
        registerDetailsForm.style.display = 'block'; // Show the form
        break;
    case "Cancelled": captureStatusMessage.textContent = 'Face capture cancelled.'; capturedEncoding = null; break;
    case "Timeout": let message = `No face detected after ${MAX_CAPTURE_ATTEMPTS} attempts. Make sure camera green square detection recognized you. And please try again.`;
          captureStatusMessage.textContent = message ; capturedEncoding = null; break;
    case "Error": capturedEncoding = null; break; // Error display is handled by the error_handler function
    default: captureStatusMessage.textContent = 'Capture stopped.'; capturedEncoding = null;}
}

async function pollCaptureFace(MAX_CAPTURE_ATTEMPTS) {
  if (!isCapturing) return; // Stop if cancelled between intervals

  captureAttemptCount++;

  if (captureAttemptCount > MAX_CAPTURE_ATTEMPTS) {stopCaptureProcess("Timeout",null,MAX_CAPTURE_ATTEMPTS); return;} // Stop if max attempts reached

  try { const res = await axios.get('/capture_face');
      if (res?.data?.status === 'success') {stopCaptureProcess("Success", res.data);} // Face found! Stop polling and process the success 
      else if (res?.data?.status === 'no_face') {captureStatusMessage.textContent =`Searching for face... (Attempt ${captureAttemptCount}/${MAX_CAPTURE_ATTEMPTS})`;} // No face found in this attempt, loop will continue via setInterval
      else {throw new Error("Process successful. But Internal Unexpected response so Face detecting stopped. Is the picture preview shows on screen?");} } // Unexpected success response format
  catch (error) {stopCaptureProcess("Error"); handleError_textcontext(error, captureStatusMessage, "capturing face", startCaptureBtn, `during Face capture attempt, number attempts completed: ${captureAttemptCount}:`); } // Stop polling on significant errors and handle the error
  }

function startCaptureProcess() {
  if (isCapturing) return; // Prevent multiple starts
  const POLLING_INTERVAL_MS = parseInt(document.getElementById("capture-interval").value, 10) || 3000; // Default to 3 seconds and use math.floor to force integer
  const MAX_CAPTURE_ATTEMPTS = parseInt(document.getElementById("capture-attempts").value, 10) || 20; // Default to 20 attempts and use math.floor to force integer
  console.log(`Polling interval: ${POLLING_INTERVAL_MS} ms, Max attempts: ${MAX_CAPTURE_ATTEMPTS}`);
  
  if(!validate_poll_configs(POLLING_INTERVAL_MS, MAX_CAPTURE_ATTEMPTS)) return; // Exit if invalid inputs
  
  console.log(`Starting capture process... Interval=${POLLING_INTERVAL_MS}ms, Max Attempts=${MAX_CAPTURE_ATTEMPTS}`);
  isCapturing = true;
  captureAttemptCount = 0;
  capturedEncoding = null; // Clear previous encoding
  
  // Reset UI
  captureStatusMessage.textContent = 'Initializing capture...';
  facePreviewImg.style.display = 'none'; facePreviewImg.src = ''; // resent image element
  registerStatusMessage.textContent = ''; registerDetailsForm.style.display = 'none'; // Clear register message & Hide registration form
  startCaptureBtn.disabled = true; startCaptureBtn.style.display = 'none'; cancelCaptureBtn.style.display = 'inline-block'; // Disable and hide start capture button & Show cancel button
  captureSpinner.style.display = 'block';

  // Start polling
  pollCaptureFace(MAX_CAPTURE_ATTEMPTS); // Run first attempt immediately
  pollingIntervalId = setInterval(() => pollCaptureFace(MAX_CAPTURE_ATTEMPTS), POLLING_INTERVAL_MS); } // create an interval object that will loop pollCaptureFace function every POLLING_INTERVAL_MS milliseconds

// (listeners for face capture)
startCaptureBtn.addEventListener('click', startCaptureProcess);
cancelCaptureBtn.addEventListener('click', () => stopCaptureProcess("Cancelled"));
// ----------------------------------------------------------------------------------------------------------------------------------------------------------

// --- Registration Logic ---
const registerDetailsForm = document.getElementById('register-details-form');

const firstNameInput = document.getElementById('first-name');
const lastNameInput = document.getElementById('last-name');
const firstNameError = document.getElementById('first-name-error');
const lastNameError = document.getElementById('last-name-error');

const registerFaceBtn = document.getElementById('register-face-btn');
const registerStatusMessage = document.getElementById('register-status-message');


registerDetailsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  registerFaceBtn.disabled = true;
  registerStatusMessage.textContent = 'Registering...';

  const firstName = firstNameInput.value.trim().replace(/\s+/g, ' '); 
  const lastName = lastNameInput.value.trim().replace(/\s+/g, ' ');

  // 1. Frontend Validation
  if (!validate_NameInputs(firstNameInput,lastNameInput,firstNameError,lastNameError,registerFaceBtn)) {registerStatusMessage.textContent = 'Please correct name errors.'; return;}
  // 2. Check if encoding was captured
  if (!capturedEncoding) {registerStatusMessage.textContent = 'Error: No face encoding was captured. Please capture first.'; registerFaceBtn.disabled = false; return;}
  // 3. API Call to register the face
  try {
      const payload = {first_name: firstName, last_name: lastName, encoding: capturedEncoding }; // Send the Names and the stored face encoding list
      const res = await axios.post('/register_face', payload);

      if (res?.data?.status === 'success') {
          registerStatusMessage.textContent = res.data.message || `Face registered: ${firstName} ${lastName}`; registerDetailsForm.reset(); registerDetailsForm.style.display = 'none'; // Clear and Hide form
          facePreviewImg.style.display = 'none'; // Hide preview
          capturedEncoding = null; // Clear captured encoding
          fetchFaces(); // Refresh list
          startCaptureBtn.disabled = false; } // Re-enable capture button
      else {console.error('Unexpected response:', res.data);
        throw new Error('Registration completed with unexpected response. Check that the new registertion exits properly');}} // Handle unexpected success response format
  catch (error) {handleError_textcontext(error, registerStatusMessage, "registering face",registerFaceBtn, 'during face registration:');}
});

// ---------------------------------------------------------------------------------------------------------------------
// --- Face List Logic ---
const refreshFacesBtn = document.getElementById('refresh-faces');
const facesListEl = document.getElementById('faces-list');

async function fetchFaces() {
  refreshFacesBtn.disabled = true;
  facesListEl.innerHTML = 'Loading...';
  
  try { const res = await axios.get('/list_faces');
        facesListEl.innerHTML = '';
      if (!res?.data || !res.data?.faces || !Array.isArray(res.data.faces)) {throw new Error('Unexpected response format: faces should be an array');} // Check if the response proper type
      if (res.data.faces && res.data.faces.length) {
          const fragment = document.createDocumentFragment();
          res.data.faces.forEach(face => {
              const li = document.createElement('li');
              // Safely construct HTML or use textContent primarily
              li.textContent = `ID: ${face.id}, Name: ${face.first_name} ${face.last_name}, Created: ${new Date(face.created_at).toLocaleString()}`;
              fragment.appendChild(li);
        });
          facesListEl.appendChild(fragment);} //Add the fragment and Re-enable button 
      else {const li = document.createElement('li'); li.textContent = 'No faces registered'; facesListEl.appendChild(li);} refreshFacesBtn.disabled = false;} // Button enabled after if-else
  catch (error) {facesListEl.innerHTML = ''; const li = document.createElement('li'); facesListEl.appendChild(li);
                 handleError_textcontext(error, li, "listing faces", refreshFacesBtn, 'While fetching faces:');} }

// (listeners for face list)
refreshFacesBtn.addEventListener('click', () => {fetchFaces();});
window.addEventListener('load', () => {
  fetchFaces(); // Initial fetch on page load
  // Set initial UI state
  registerDetailsForm.style.display = 'none';
  cancelCaptureBtn.style.display = 'none';
  facePreviewImg.style.display = 'none';
  startCaptureBtn.style.display = 'inline-block'; startCaptureBtn.disabled = false; });
// ------------------------------------------------------------------------------------

// --- Delete Face Logic ---
const deleteFaceForm = document.getElementById('delete-face-form');
const faceIdInput = document.getElementById('delete-face-id');
const deleteBtn = document.getElementById('delete-face-btn');

const deleteMessageEl = document.getElementById('delete-message');
const faceIdErrorEl = document.getElementById('face-id-error');

deleteFaceForm.addEventListener('submit', async (e) => { e.preventDefault();
  deleteBtn.disabled = true;
  const faceId = faceIdInput.value;
  // Clear previous messages
  deleteMessageEl.textContent = '';
  faceIdErrorEl.textContent = '';

  try { // Validate face ID input type
      if (!faceIdInput.checkValidity()) {faceIdErrorEl.textContent = 'Invalid Face ID. It must be a positive integer.'; deleteBtn.disabled = false; return;}
      if (confirm(`Are you sure you want to delete the Registered face ${faceId}? This action cannot be undone.`)) {
          
            const res = await axios.delete(`/delete_face/${faceId}`);
          if (res) {alert(res.data?.message || `Face ID ${faceId} deleted successfully.`); faceIdInput.value = ''; fetchFaces(); deleteBtn.disabled = false; }} // Refresh the face list after deletion
      else {alert(`Deletion of face ID ${faceId} was cancelled.`); deleteBtn.disabled = false;}} 
  catch (error) {handleError_textcontext(error, deleteMessageEl,"to Delete face", deleteBtn, 'While deleting face:');} 
});

// ------------------------------------------------------------------------------------------------------------------------------------------
// ------------------------------------------------------------------------------------------------------------------------------------------  

//------- Refresh live-feed --------------------------
const refreshLiveFeedBtn = document.getElementById('refresh-livefeed-btn');
const liveFeedImg = document.getElementById('live-feed');
const liveFresh = document.getElementById('livefresh');
const disappearFeedbtn = document.getElementById('disappear-feed-btn');
const appearFeedbtn = document.getElementById('appear-feed-btn');

// (listener for Live-Feed refresh)
refreshLiveFeedBtn.addEventListener('click', () => {
  refreshLiveFeedBtn.disabled = true; // defend the server from abuse
  liveFresh.textContent = "Refreshing feed, please wait..."; 
  liveFeedImg.onload = () => {liveFresh.textContent = "";};
  liveFeedImg.onerror = () => {liveFresh.textContent = "Live feed failed to load. Refresh page or in 2 second press the refresh feed button.";};
  liveFeedImg.src = `/register_video_feed?timestamp=${new Date().getTime()}`; // Append a timestamp to bypass any caching freeze
  setTimeout(() => {refreshLiveFeedBtn.disabled = false;}, 2000); });
// Hide and show live feed
disappearFeedbtn.addEventListener('click', () => {
    liveFeedImg.style.display = 'none'; disappearFeedbtn.style.display = 'none'; refreshLiveFeedBtn.style.display = 'none'; 
    liveFresh.textContent = "Press Show live feed button to show the live feed again.";
    appearFeedbtn.style.display="inline-block";}); // Hide live feed and show appear button
appearFeedbtn.addEventListener('click', () => {
    liveFeedImg.style.display = 'block'; disappearFeedbtn.style.display = 'inline-block'; refreshLiveFeedBtn.style.display = 'inline-block';
    liveFresh.textContent = "If livefeed doesn't show, Press refresh button to show the live feed again.";
    appearFeedbtn.style.display="none";});


    // --- Possible Event Listeners ---
// (listeners for Register Face)
// document.getElementById("capture-attempts").addEventListener("input", (e) => {const value = parseInt(e.target.value, 10); e.target.value = value || "";}); // Force to integer and prevent non-number inputs
// document.getElementById("capture-interval").addEventListener("input", (e) => {const value = parseInt(e.target.value, 10); e.target.value = value || "";});
// document.getElementById("capture-attempts").addEventListener("input", (e) => {e.target.value = e.target.value.replace(/[^0-9]/g,'');}); // delete all non-number inputs
// document.getElementById("capture-interval").addEventListener("input", (e) => {e.target.value = e.target.value.replace(/[^0-9]/g,'');});
