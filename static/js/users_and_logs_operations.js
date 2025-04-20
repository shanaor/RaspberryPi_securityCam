import axios from 'https://esm.sh/axios';
axios.defaults.withCredentials = true;

// CONFIG
// Function to handle error messages and site redirection
function handleError_textcontext(error_var,htmltext,failed_action,button) {    
  if (error_var.response) { // check if there is an error response from the server
    const status = error_var.response?.status;
    const detail = error_var.response?.data?.detail;
    
    // Check for specific status codes and handle accordingly
    if      (status === 400) {htmltext.textContent = `${detail}`;}
    else if (status === 401) {alert(`${detail}`); window.location.href = '/Login.html';} // Redirect to login to unauthurized users
    else if (status === 403) {alert(`${detail}`); window.location.href = '/Livefeed.html';} // Redirect to livefeed to unauthurized action, to penalize bad behavior
    else if (status === 404) {htmltext.textContent = `${detail}`; button.disabled = false;} // Re-enable button after 404 error
    else if (status === 409) {htmltext.textContent = `${detail}`; button.disabled = false;}
    else if (status === 500) {htmltext.textContent = `${detail}`;}
    else {htmltext.textContent = `Failed ${failed_action}. Please REFRESH page and try again.`;}
  // Setup error or other client-side issue
  } else if (error_var.request) {htmltext.textContent = 'Network Error: Could not reach server. REFRESH page and try again';}
    else {htmltext.textContent = `Client Error: ${error_var.message}. REFRESH page and try again`;}}; // Network connection error

function user_password_validation(username,password,registerError) {
    // Validate username (3-20 chars, alphanumeric + space/underscore)
    if (!/^[a-zA-Z0-9_ ]{3,20}$/.test(username)) { registerError.textContent = 'Username must be 3-20 characters (alphanumeric, space, underscore)'; return false; }
    // Validate password (8-64 chars, with number, lowercase, uppercase, special char)
    if (!/^[a-zA-Z0-9@#%^&+=]{8,64}$/.test(password) || 
        !/[0-9]/.test(password) || !/[a-z]/.test(password) || 
        !/[A-Z]/.test(password) || !/[@#%^&+=]/.test(password)) {
        registerError.textContent = 'Password must be 8-64 characters with a number, lowercase, uppercase, and special character (@#%^&+=)'; return false; }
    return true; // If both validations pass
  }
// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------

// Register New User
const registerForm = document.getElementById('register-form');
const registerBtn = document.getElementById('registerbtn');
const registerError = document.getElementById('register-error');

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    registerError.textContent = 'Processing...';
    registerBtn.disabled = true;
  
  try {
      const username = document.getElementById('reg-username').value;
      const password = document.getElementById('reg-password').value;
      if (!user_password_validation(username,password,registerError)) {
        registerBtn.disabled = false; // Re-enable button if validation fails
        return; } // Stop registration execution if validation fails

      const res = await axios.post('/register_user/', { username, password });
      registerError.textContent = res.data.message;
      registerForm.reset();
      await fetchUsers();
      registerBtn.disabled = false;
      registerError.textContent = 'User registered successfully';
  } catch (error_register) {
        console.error('Error registering user in users_and_logs_operations.js:', error_register);
        const failed_action = "to Register user";
        handleError_textcontext(error_register,registerError,failed_action,registerBtn);}
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
        const usersError = document.getElementById('users-management');
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = async () => {
          if (confirm(`Are you sure you want to delete user ${id}?`)) {
                deleteBtn.disabled = true; // Disable the button to prevent harrasing the backend
                usersError.textContent = 'Processing...';
              try {
                await axios.delete(`/delete/${id}/`);
                alert(`User ${id} deleted`);
                usersError.textContent = '';
                deleteBtn.disabled = false; // Re-enable button after deletion
                fetchUsers();
            } catch (error_delete) {
                console.error('Error deleting user in users_and_logs_operations.js:', error_delete);
                const failed_action = "to delete user";
                handleError_textcontext(error_delete,usersError,failed_action,deleteBtn);}
        } else {alert(`Deletion of user ${id} was cancelled.`); deleteBtn.disabled = false;} // Re-enable button if deletion is cancelled
      };
        
        // Activate Button
        const activateBtn = document.createElement('button');
        const activeMessage = document.getElementById('users-management'); // element saved again with another const just for the sake of easy reading
        activateBtn.textContent = 'Activate';
        activateBtn.disabled = is_active === 1; // if True that is_active = 1 then it transfer the "True" to the button
        activateBtn.onclick = async () => {
          activateBtn.disabled = true; // this prevents multiple clicks in situations that .disabled=is_active doesnt cover, like before changing states
          activeMessage.textContent = 'Processing...'
        try {
          await axios.put(`/activate/${id}/`);
          activeMessage.textContent = `User ${id} activated`;
          fetchUsers();
          activateBtn.disabled = false;
      } catch (error_activate) {
          console.error('Error activating user in users_and_logs_operations.js:', error_activate);
          const failed_action = "to activate user";
          handleError_textcontext(error_activate,activeMessage,failed_action,activateBtn);}
    };
        
        // Deactivate Button
        const deactivateMessage = document.getElementById('users-management'); // again saved, to avoid confusion, due to different message elements
        const deactivateBtn = document.createElement('button');
        deactivateBtn.textContent = 'Deactivate';
        deactivateBtn.disabled = is_active === 0; // Disable if already inactive to prevent multi requests
        deactivateBtn.onclick = async () => {
          deactivateBtn.disabled = true;
          deactivateMessage.textContent = 'Processing...'
        try {
          await axios.put(`/deactivate/${id}/`);
          deactivateMessage.textContent = `User ${id} deactivated`;
          fetchUsers();      
          deactivateBtn.disabled = false;
      } catch (error_deactivate) {
          console.error('Error deactivating user in users_and_logs_operations.js:', error_deactivate);
          const failed_action = "to deactivate user";
          handleError_textcontext(error_deactivate,deactivateMessage,failed_action,deactivateBtn);}
        };

        li.append(' ', deleteBtn, ' ', activateBtn, ' ', deactivateBtn);
        fragmentUser.appendChild(li);
      });
      usersListEl.appendChild(fragmentUser);
      refreshUsersBtn.disabled = false; // Re-enable button after successful userlist fetch
  } catch (error_refresh) {
        console.error('Error refresh user in users_and_logs_operations.js:', error_refresh);
        const failed_action = "to load users";
        handleError_textcontext(error_refresh,usersListEl,failed_action,refreshUsersBtn);} 
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
  logsListEl.innerHTML = 'Loading...';
  const day = document.getElementById('log-day').value;
  const month = document.getElementById('log-month').value;
  const year = document.getElementById('log-year').value;
  
try {
    if (day && (!Number.isInteger(Number(day)) || day < 1 || day > 31)) {
      logsError.textContent = 'Day must be an integer between 1 and 31'; logFetchBtn.disabled = false;
      return; }

    if (month && (!Number.isInteger(Number(month)) || month < 1 || month > 12)) {
      logsError.textContent = 'Month must be an integer between 1 and 12'; logFetchBtn.disabled = false;
      return; }

    if (year && (!Number.isInteger(Number(year)) || year < 1900 || year > 2100)) {
      logsError.textContent = 'Year must be an integer between 1900 and 2100'; logFetchBtn.disabled = false;
      return; }

    let url = '/event-logs/?';
    if(day) url += `day=${day}&`;
    if(month) url += `month=${month}&`;
    if(year) url += `year=${year}&`;
    
      const res = await axios.get(url);
      logsListEl.innerHTML = '';
      const fragment = document.createDocumentFragment();
      res.data.forEach(log => {
        const li = document.createElement('li');
        li.textContent = JSON.stringify(log);
        fragment.appendChild(li);
      });
      logsListEl.appendChild(fragment);
      logFetchBtn.disabled = false;
  } catch (error_logs) {
    console.error('Error event-logs in users_and_logs_operations.js:', error_logs);
    const failed_action = "to load logs";
    handleError_textcontext(error_logs,logsListEl,failed_action,logFetchBtn);}
  });