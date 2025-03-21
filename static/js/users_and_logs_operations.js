import axios from 'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js';
axios.defaults.withCredentials = true;

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

  // Validate username (3-20 chars, alphanumeric + space/underscore)
if (!/^[a-zA-Z0-9_ ]{3,20}$/.test(username)) {
  registerError.textContent = 'Username must be 3-20 characters (alphanumeric, space, underscore)';
  return;
}
// Validate password (8-64 chars, with number, lowercase, uppercase, special char)
if (!/^[a-zA-Z0-9@#%^&+=]{8,64}$/.test(password) || 
    !/[0-9]/.test(password) || !/[a-z]/.test(password) || 
    !/[A-Z]/.test(password) || !/[@#%^&+=]/.test(password)) {
    registerError.textContent = 'Password must be 8-64 characters with a number, lowercase, uppercase, and special character (@#%^&+=)';
    return;
}
    const res = await axios.post('/register_user/', { username, password });
    registerError.textContent = res.data.message;
    registerForm.reset();
    await fetchUsers();
  } catch (err) {
    console.error('Error registering user in users_and_logs_operations.js:', error);
    registerError.textContent = err.response?.data?.detail || 'Registration failed';
  } finally {
  registerBtn.disabled = false;
}});

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
      const usersError = document.getElementById('users-error');
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = 'Delete';
      deleteBtn.onclick = async () => {
        if (confirm(`Are you sure you want to delete user ${id}?`)) {
          deleteBtn.disabled = true; // Disable the button to prevent harrasing the backend
          usersError.textContent = 'Processing...'
        try {
          await axios.delete(`/delete/${id}/`);
          usersError.textContent = `User ${id} deleted`;
          fetchUsers();
        } catch (err) {
          console.error('Error deleting user in users_and_logs_operations.js:', error);
          deleteBtn.disabled = false; // Re-enable button if the request fails
          if (err.response.status === 404) {
            usersError.textContent = 'User not found';
        } else {
          usersError.textContent = err.response?.data?.detail || 'Delete failed';
        } 
      }}};
      
      // Activate Button
      const activateBtn = document.createElement('button');
      const activeMessage = document.getElementById('users-error'); // element saved again with another const just for the sake of easy reading
      activateBtn.textContent = 'Activate';
      activateBtn.disabled = is_active === 1; // if True that is_active = 1 then it transfer the "True" to the button
      activateBtn.onclick = async () => {
        activateBtn.disabled = true; // this prevents multiple clicks in situations that .disabled=is_active doesnt cover, like before changing states
        activeMessage.textContent = 'Processing...'
        try {
          await axios.put(`/activate/${id}/`);
          activeMessage.textContent = `User ${id} activated`;
          fetchUsers();
        } catch (err) {
          console.error('Error activating user in users_and_logs_operations.js:', error);
          activateBtn.disabled = false;
          activeMessage.textContent = err.response?.data?.detail || 'Activate failed';
        }
      };
      
      // Deactivate Button
      const deactivateMessage = document.getElementById('users-error'); // again saved, to avoid confusion, due to different message elements
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
        } catch (err) {
          console.error('Error deactivating user in users_and_logs_operations.js:', error);
          deactivateBtn.disabled = false;
          deactivateMessage.textContent = err.response?.data?.detail || 'Deactivate failed';
        }
      };
      li.append(' ', deleteBtn, ' ', activateBtn, ' ', deactivateBtn);
      fragmentUser.appendChild(li);
    });
    usersListEl.appendChild(fragmentUser);
  } catch (err) {
    console.error('Error refresh user in users_and_logs_operations.js:', error);
    usersListEl.innerHTML = 'Failed to load users. Please try again.';
  } finally {
  refreshUsersBtn.disabled = false; // release button after success, to allow another user fetch
}}
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
    logsError.textContent = 'Day must be an integer between 1 and 31';
    return;
  }
  if (month && (!Number.isInteger(Number(month)) || month < 1 || month > 12)) {
    logsError.textContent = 'Month must be an integer between 1 and 12';
    return;
  }
  if (year && (!Number.isInteger(Number(year)) || year < 1900 || year > 2100)) {
    logsError.textContent = 'Year must be an integer between 1900 and 2100';
    return;
  }

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
  } catch (err) {
    console.error('Error event-logs in users_and_logs_operations.js:', error);
    logsListEl.innerHTML = err.response?.status === 404 ? 'No logs found for this date' : 'Error loading logs';
  } finally {
  logFetchBtn.disabled = false;
  }
});