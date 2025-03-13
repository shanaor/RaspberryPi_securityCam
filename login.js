import axios from 'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js';

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const errorMessage = document.getElementById('error-message');

  try {
    const response = await axios.post('/login', { username, password });

    // Check if login was successful
    if (response.status === 200 && response.data.message === "Login successful") {
      // Redirect to Livefeed.html after successful login
      window.location.href = "Livefeed.html";
    }
  } catch (error) {
    console.error('Invalid credentials', error);    
    if (errorMessage) {
      errorMessage.textContent = 'Invalid username or password';
    }
  }
});
