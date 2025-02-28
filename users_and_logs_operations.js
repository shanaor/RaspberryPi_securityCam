import axios from 'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js';

// Register New User
const registerForm = document.getElementById('register-form');
registerForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('reg-username').value;
  const password = document.getElementById('reg-password').value;
  try {
    const res = await axios.post('/register_user/', { username, password });
    alert(res.data.message);
    registerForm.reset();
    fetchUsers();
  } catch (err) {
    alert(err.response.data.detail || 'Registration failed');
  }
});

// Fetch and Display Registered Users
const usersListEl = document.getElementById('users');
const refreshUsersBtn = document.getElementById('refresh-users');
async function fetchUsers() {
  try {
    const res = await axios.get('/userslist/');
    usersListEl.innerHTML = '';
    res.data.forEach(user => {
      const [id, username, is_active] = user;
      const li = document.createElement('li');
      li.textContent = `ID: ${id}, Username: ${username}, Active: ${is_active}`;
      
      // Delete Button
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = 'Delete';
      deleteBtn.onclick = async () => {
        try {
          await axios.delete(`/delete/${id}/`);
          alert(`User ${id} deleted`);
          fetchUsers();
        } catch (err) {
          alert(err.response.data.detail || 'Delete failed');
        }
      };
      
      // Activate Button
      const activateBtn = document.createElement('button');
      activateBtn.textContent = 'Activate';
      activateBtn.onclick = async () => {
        try {
          await axios.put(`/activate/${id}/`);
          alert(`User ${id} activated`);
          fetchUsers();
        } catch (err) {
          alert(err.response.data.detail || 'Activate failed');
        }
      };
      
      // Deactivate Button
      const deactivateBtn = document.createElement('button');
      deactivateBtn.textContent = 'Deactivate';
      deactivateBtn.onclick = async () => {
        try {
          await axios.put(`/deactivate/${id}/`);
          alert(`User ${id} deactivated`);
          fetchUsers();
        } catch (err) {
          alert(err.response.data.detail || 'Deactivate failed');
        }
      };
      
      li.append(' ', deleteBtn, ' ', activateBtn, ' ', deactivateBtn);
      usersListEl.appendChild(li);
    });
  } catch (err) {
    usersListEl.innerHTML = 'Error loading users';
  }
}
refreshUsersBtn.addEventListener('click', fetchUsers);
fetchUsers();

// Fetch Event Logs
const logsForm = document.getElementById('logs-form');
const logsListEl = document.getElementById('logs');
logsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const day = document.getElementById('log-day').value;
  const month = document.getElementById('log-month').value;
  const year = document.getElementById('log-year').value;
  
  let url = '/event-logs/?';
  if(day) url += `day=${day}&`;
  if(month) url += `month=${month}&`;
  if(year) url += `year=${year}&`;
  
  try {
    const res = await axios.get(url);
    logsListEl.innerHTML = '';
    res.data.forEach(log => {
      const li = document.createElement('li');
      li.textContent = JSON.stringify(log);
      logsListEl.appendChild(li);
    });
  } catch (err) {
    logsListEl.innerHTML = 'Error loading logs';
  }
});
