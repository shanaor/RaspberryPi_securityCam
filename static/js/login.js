import axios from 'https://esm.sh/axios';
axios.defaults.withCredentials = true;

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
    const username = document.getElementById('username');
    const password = document.getElementById('password');
    const errorMessage = document.getElementById('error-message');
    const submitButton = e.target.querySelector('button[type="submit"]');
    submitButton.disabled = true; // Disabling button to prevent multiple clicks
    // Clear previous error messages
    errorMessage.textContent = '';

try {
    // was offered to add this validation check 
    // due to possible miss of html regrex check by different broswers for many reasons 

      // Validate username
      if (!username.checkValidity()) { errorMessage.textContent = 'Invalid username. It must be 3-20 characters long and contain only letters, numbers, underscores, or spaces.'; submitButton.disabled = false; return;}
      // Validate password
      const passwordValue = password.value;
      if (!password.checkValidity()) { errorMessage.textContent = 'Invalid password. It must be 8-64 characters long and contain only letters, numbers, and special characters (@#%^&+=).'; submitButton.disabled = false; return;}
      // Additional password complexity checks
      if (!/[0-9]/.test(passwordValue)) { errorMessage.textContent = 'Password must contain at least one number.'; submitButton.disabled = false; return;}
      if (!/[a-z]/.test(passwordValue)) { errorMessage.textContent = 'Password must contain at least one lowercase letter.'; submitButton.disabled = false; return;}
      if (!/[A-Z]/.test(passwordValue)) { errorMessage.textContent = 'Password must contain at least one uppercase letter.'; submitButton.disabled = false; return;}
      if (!/[@#%^&+=]/.test(passwordValue)) { errorMessage.textContent = 'Password must contain at least one special character (@#%^&+=).'; submitButton.disabled = false; return;}

    // Adding loading state to button
    submitButton.classList.add('loading');
    errorMessage.textContent = 'Please wait...';
      // Submit to server
      
        const response = await axios.post('/login', { username: username.value, password: password.value });

        if (response.status === 200 && response.data.message === "Login successful") {window.location.href = "/Livefeed.html";}} 
catch (error) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail
        // Check for 401 (Invalid credentials), Check for 500 (Internal server error)
      if (status === 401) {console.error('Login credentials error in login.js:', error); errorMessage.textContent = detail;} 
      else if (status === 403) {console.error('Unauthorized access.js:', error); errorMessage.textContent = detail;}
      else if (status === 500) {console.error('Login Internal server error in login.js:', error); errorMessage.textContent = detail;} 
        // Handle any other unexpected errors
      else if (error.request) {console.error('No response received from server:', error.request); errorMessage.textContent = "Network error: Unable to reach the server. Please check your connection.";}
      else {console.error('Login unexpected error in login.js:', error); errorMessage.textContent = 'An unexpected error occurred, try again';}} 
finally {submitButton.classList.remove('loading'); submitButton.disabled = false;} // Removing loading state after request completes and Re-enabling the button
});