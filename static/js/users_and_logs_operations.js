import axios from 'https://esm.sh/axios';
axios.defaults.withCredentials = true;

// CONFIG
// Function to handle error messages and site redirection
function handleError_textcontext(error_var,htmltext,failed_action,button,errormsg) {    
  console.error(`Error in users_and_logs_operations.js while ${errormsg} :`, error_var);
  
  if (error_var.response) { // check if there is an error response from the server
    const status = error_var.response?.status;
    const detail = error_var.response?.data?.detail;
    
    // Check for specific status codes and handle accordingly
    if      (status === 400) {htmltext.textContent = `${detail}`; button.disabled = false;} // Re-enable button after 400 error
    else if (status === 401) {alert(`${detail}`); window.location.href = '/Login.html';} // Redirect to login to unauthurized users
    else if (status === 403) {alert(`${detail}`); window.location.href = '/Livefeed.html';} // Redirect to livefeed to unauthurized action, to penalize bad behavior
    else if (status === 404) {htmltext.textContent = `${detail}`; button.disabled = false;} // Re-enable button after 404 error
    else if (status === 409) {htmltext.textContent = `${detail}`; button.disabled = false;}
    else if (status === 500) {htmltext.textContent = `${detail}`;}
    else {htmltext.textContent = `Failed ${failed_action}. Please REFRESH page and try again.`;}
  // Setup error or other client-side issue
  } else if (error_var.request) {htmltext.textContent = 'Network Error: Could not reach server. REFRESH page and try again';}
    else {htmltext.textContent = `Client Error: ${error_var.message}. REFRESH page and try again`;}}; // Network connection error

function username_validation(username,registerError,registerMsg) {
    registerError.textContent = '';
    registerMsg.textContent = '';
    // Validate username (3-20 chars, alphanumeric + space/underscore)
    if (!/^[a-zA-Z0-9_ ]{3,20}$/.test(username)) {registerMsg.classList.remove("success-message"); registerError.textContent = 'Username must be 3-20 characters (alphanumeric, space, underscore)'; }
    else {registerMsg.classList.add("success-message"); registerMsg.textContent = 'seems good!!';}}

function password_validation(password,registerError,registerMsg) {
    registerError.textContent = '';
    registerMsg.textContent = '';
    // Validate password (8-64 chars, with number, lowercase, uppercase, special char)
    if (!/^[a-zA-Z0-9@#%^&+=]{8,64}$/.test(password) || 
        !/[0-9]/.test(password) || !/[a-z]/.test(password) || 
        !/[A-Z]/.test(password) || !/[@#%^&+=]/.test(password)) {registerMsg.classList.remove("success-message");
        registerError.textContent = 'Password must be 8-64 characters with a number, lowercase, uppercase, and special character (@#%^&+=)';}
    else {registerMsg.classList.add("success-message"); registerMsg.textContent = 'seems good!!';}}

function user_name_password_validation(username,password,registerError) {
    // Validate username (3-20 chars, alphanumeric + space/underscore)
    if (!/^[a-zA-Z0-9_ ]{3,20}$/.test(username)) { registerError.textContent = 'Username must be 3-20 characters (alphanumeric, space, underscore)'; return false; }
    // Validate password (8-64 chars, with number, lowercase, uppercase, special char)
    if (!/^[a-zA-Z0-9@#%^&+=]{8,64}$/.test(password) || !/[0-9]/.test(password) || !/[a-z]/.test(password) || !/[A-Z]/.test(password) || !/[@#%^&+=]/.test(password)) {
        registerError.textContent = 'Password must be 8-64 characters with a number, lowercase, uppercase, and special character (@#%^&+=)'; return false; }
    return true;} // If both validations pass
// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------

// Register New User
const registerForm = document.getElementById('register-form');
const registerBtn = document.getElementById('registerbtn');
const registerError = document.getElementById('register-error');
const registerMsg = document.getElementById('register-message');

 // Adding success message class to the message element for styling
document.getElementById('reg-username').addEventListener('input', () => {
  username_validation( document.getElementById('reg-username').value,registerError,registerMsg);}); // Validate username Live on input
document.getElementById('reg-password').addEventListener('input', () => {
  password_validation( document.getElementById('reg-password').value,registerError,registerMsg);}); // Validate password Live on input

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    registerMsg.classList.remove("success-message");
    registerError.textContent = '';
    registerMsg.textContent = 'Processing...';
    registerBtn.disabled = true;
  
  try {
      const username = document.getElementById('reg-username').value;
      const password = document.getElementById('reg-password').value;
      if (!user_name_password_validation(username,password,registerError)) {registerBtn.disabled = false; return;} // Validate username and password

      const res = await axios.post('/register_user/', { username, password });
      registerMsg.classList.add("success-message");
      registerMsg.textContent = res.data.message || 'User registered successfully!';
      setTimeout(async () => {registerForm.reset(); registerMsg.textContent =''; registerMsg.classList.remove("success-message"); await fetchUsers(); }, 3000); // 3-second delay
      registerBtn.disabled = false;} 
  catch (error_register) {registerMsg.textContent = ''; handleError_textcontext(error_register,registerError,"to Register user",registerBtn,"Registering user");}
    });

// Fetch and Display Registered Users
const usersListEl = document.getElementById('users');
const refreshUsersBtn = document.getElementById('refresh-users');
async function fetchUsers() {
  refreshUsersBtn.disabled = true; // disable button, prevent server harrasment
  usersListEl.innerHTML = 'Loading...';
 
  try {
      const res = await axios.get('/userslist/');
      usersListEl.innerHTML = '';
      const fragmentUser = document.createDocumentFragment();
      res.data.forEach(user => {
        const [id, username, is_active] = user;
        const li = document.createElement('li');
        li.textContent = `ID: ${id}, Username: ${username}, Active: ${is_active}`;
        
        // Delete Button
        const usersError = document.getElementById('users-management-error');
        const usersMsg = document.getElementById('users-management');
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.classList.add('redbtn'); // Adding red button style class from the CSS

        deleteBtn.onclick = async () => {
          usersError.textContent = ''; // Clear any previous error messages
          if (confirm(`Are you sure you want to delete User: ${username}, ID: ${id}?`)) {
                deleteBtn.disabled = true; // Disable the button to prevent harrasing the backend
                usersMsg.textContent = 'Processing...';
              try {
                await axios.delete(`/delete/${id}/`);
                alert(`User: ${username}, ID: ${id} deleted`);
                usersMsg.textContent = '';
                deleteBtn.disabled = false; // Re-enable button after deletion
                await fetchUsers();} 
              catch (error_delete) {usersMsg.textContent=''; handleError_textcontext(error_delete,usersError,"to delete user",deleteBtn,'Deleting user');}} 
          else {usersMsg.textContent=''; alert(`Deletion of User: ${username}, ID: ${id} was cancelled.`); deleteBtn.disabled = false;} // Re-enable button if deletion is cancelled
        };
        
        // Activate Button
        const activateBtn = document.createElement('button');
        const activeMessage = document.getElementById('users-management'); // element saved again with another const just for the sake of easy reading
        const activeError = document.getElementById('users-management-error');
        activateBtn.textContent = 'Activate';
        activateBtn.disabled = is_active === 1; // if True that is_active = 1 then it transfer the "True" to the button
        activateBtn.onclick = async () => {
          activateBtn.disabled = true; // this prevents multiple clicks in situations that .disabled=is_active doesnt cover, like before changing states
          activeError.textContent = ''; // Clear any previous error messages
          activeMessage.textContent = 'Processing...'
        try {
          await axios.put(`/activate/${id}/`);
          activeMessage.classList.add("success-message");
          activeMessage.textContent = `User: ${username}, ID: ${id} activated`;
          setTimeout( async () => {activeMessage.textContent = ''; activeMessage.classList.remove("success-message"); await fetchUsers();}, 3000); // 3-second delay
          activateBtn.disabled = false;} 
        catch (error_activate) {activeMessage.textContent = ''; handleError_textcontext(error_activate,activeError,"to activate user",activateBtn,'Activating user');}
      };
        
        // Deactivate Button
        const deactivateError = document.getElementById('users-management-error');
        const deactivateMessage = document.getElementById('users-management'); // again saved, to avoid confusion, due to different message elements
        const deactivateBtn = document.createElement('button');
        deactivateBtn.textContent = 'Deactivate';
        deactivateBtn.classList.add('secondary'); // Adding gray button style class from the CSS
        deactivateBtn.disabled = is_active === 0; // Disable if already inactive to prevent multi requests
        deactivateBtn.onclick = async () => {
          deactivateBtn.disabled = true;
          deactivateMessage.textContent = 'Processing...'
          deactivateError.textContent = ''; // Clear any previous error messages
        
        try {
          await axios.put(`/deactivate/${id}/`);
          deactivateMessage.classList.add("success-message");
          deactivateMessage.textContent = `User: ${username}, ID: ${id} deactivated`;
          setTimeout( async () => {deactivateMessage.textContent = ``; deactivateMessage.classList.remove("success-message"); await fetchUsers();}, 3000); // 3-second delay      
          deactivateBtn.disabled = false;} 
        catch (error_deactivate) {deactivateMessage.textContent = ``; handleError_textcontext(error_deactivate,deactivateError,"to deactivate user",deactivateBtn,'Deactivating user');}
        };

        li.append(' ', deleteBtn, ' ', activateBtn, ' ', deactivateBtn);
        fragmentUser.appendChild(li);
      });
      usersListEl.appendChild(fragmentUser);
      refreshUsersBtn.disabled = false;} // Re-enable button after successful userlist fetch
  catch (error_refresh) {handleError_textcontext(error_refresh,usersListEl,"to load users",refreshUsersBtn,'Refreshing users list');} 
};

refreshUsersBtn.addEventListener('click', fetchUsers);
fetchUsers();

// Fetch Event Logs
const logsError = document.getElementById('logs-error');
const logsForm = document.getElementById('logs-form');
const logsListEl = document.getElementById('logs');
const logFetchBtn = document.getElementById('logfetch');
logsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  logFetchBtn.disabled = true;
  logsError.innerHTML = "";
  logsListEl.innerHTML = 'Loading...';
  const day = document.getElementById('log-day').value;
  const month = document.getElementById('log-month').value;
  const year = document.getElementById('log-year').value;
  
  try {
      if (day && (!Number.isInteger(Number(day)) || day < 1 || day > 31)) { logsListEl.innerHTML = ''; logsError.textContent = 'Day must be an integer between 1 and 31'; setTimeout(() => {logFetchBtn.disabled = false}, 2000); //prevent quick resubmisison
        return; }

      if (month && (!Number.isInteger(Number(month)) || month < 1 || month > 12)) { logsListEl.innerHTML = ''; logsError.textContent = 'Month must be an integer between 1 and 12'; setTimeout(() => {logFetchBtn.disabled = false}, 2000); //prevent quick resubmisison
        return; }

      if (year && (!Number.isInteger(Number(year)) || year < 1900 || year > 2100)) { logsListEl.innerHTML = ''; logsError.textContent = 'Year must be an integer between 1900 and 2100'; setTimeout(() => {logFetchBtn.disabled = false}, 2000); //prevent quick resubmisison
        return; }

      let url = '/event-logs/?';
      if(day) url += `day=${day}&`;
      if(month) url += `month=${month}&`;
      if(year) url += `year=${year}&`;
      
        const res = await axios.get(url);
        logsListEl.innerHTML = '';
        const fragment = document.createDocumentFragment();
        res.data.forEach(log => {
          const [id, event_type, description, timestamp] = log;
          
          const li = document.createElement('li');
          
          const idSpan = document.createElement('span');
          idSpan.className = 'log-id';
          idSpan.textContent = `ID: ${id}`;
          
          const eventSpan = document.createElement('span');
          eventSpan.className = 'log-event';
          eventSpan.textContent = `Event: ${event_type}`;
          
          const descSpan = document.createElement('span');
          descSpan.className = 'log-description';
          descSpan.textContent = `Description: ${description}`;
          
          const timeSpan = document.createElement('span');
          timeSpan.className = 'log-timestamp';
          const formattedTimestamp = new Date(timestamp).toLocaleString('en-GB');
          timeSpan.textContent = `Timestamp: ${formattedTimestamp}`;
          
          li.append(idSpan, eventSpan, descSpan, timeSpan);
          fragment.appendChild(li);
        });
        logsListEl.appendChild(fragment);
        logFetchBtn.disabled = false;} 
  catch (error_logs) {logsListEl.innerHTML = ''; handleError_textcontext(error_logs,logsError,"to load logs",logFetchBtn,'pulling event-logs:');}
});

// //  ----- POSSIBLE FUTURE FUNCTIONALITY -----
// const params = new URLSearchParams();
// if (day) params.append('day', day);
// if (month) params.append('month', month);
// if (year) params.append('year', year);
// const url = `/event-logs/?${params.toString()}`;