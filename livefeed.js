// Refreshing livefeed by appending timestamp to bypass caching and get new request from the server
const liveFeedImg = document.getElementById('live-feed');
const refreshBtn = document.getElementById('refresh-feed');

refreshBtn.addEventListener('click', () => {
  liveFeedImg.src = `/video_feed?timestamp=${new Date().getTime()}`;
});
