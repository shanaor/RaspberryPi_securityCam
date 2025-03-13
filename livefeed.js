// DOM elements
const liveFeedImg = document.getElementById('live-feed');
const refreshBtn = document.getElementById('refresh-feed');
const statusMessage = document.getElementById('status-message');
const spinner = document.querySelector('.spinner');
const SERVER = 'https://192.168.1.195:8123';

// Function to update the live feed
function updateLiveFeed() {
    const timestamp = new Date().getTime();
    liveFeedImg.src = `${SERVER}/video_feed?timestamp=${timestamp}`;
    statusMessage.textContent = 'Loading live feed...';
    spinner.style.display = 'block';
}

// Function to handle errors and auto-refresh
function handleFeedError() {
    spinner.style.display = 'none';
    statusMessage.textContent = 'Error loading feed. Retrying in 1 second...';
    setTimeout(() => {
        updateLiveFeed();  // Retry after 1 second
    }, 1000);
}

liveFeedImg.onload = () => {
    spinner.style.display = 'none';
    // Check if the content is an image (signals sucess) or text (signals failure)
    fetch(liveFeedImg.src)
        .then(response => {
            spinner.style.display = 'none';
            const contentType = response.headers.get('Content-Type');
            if (contentType.includes('text/plain')) {
                response.text().then(text => {
                    statusMessage.textContent = text.trim();
                    liveFeedImg.style.display = 'none';
                });
            } else {
                statusMessage.textContent = '';
                liveFeedImg.style.display = 'block';
            }
        })
        .catch(() => {
            spinner.style.display = 'none';
            statusMessage.textContent = 'Connection error. Retrying...';
            handleFeedError();  // Retry on fetch failure
        });
};

// Set up event listener to track error
liveFeedImg.onerror = handleFeedError;  // Auto-refresh on error

// Manual refresh button evenlistener
refreshBtn.addEventListener('click', () => {
    updateLiveFeed();
});

// Start livefeed when the page loads eventlistener
window.addEventListener('load', () => {
    updateLiveFeed();
});