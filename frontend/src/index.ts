function sendVideoProgress(currentTime: number) {
    fetch('save-video-progress/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json', // Ustawienie nagłówka
        },
        body: JSON.stringify({
            currentTime: currentTime, 
        }),
    })
        .then((response) => {
            if (!response.ok) {
                console.error(`HTTP error! status: ${response.status}`);
                return response.json().then((data) => {
                    console.error('Error details from backend:', data);
                    throw new Error(data.error || 'Unknown error');
                });
            }
            return response.json();
        })
        .then((data) => {
            console.log('Video progress saved:', data);
        })
        .catch((error) => {
            console.error('Fetch error:', error.message);
        });
}
const videoPlayer = document.getElementById('videoPlayer') as HTMLVideoElement;

if (videoPlayer) {
    videoPlayer.addEventListener('pause', () => {
        console.log('Paused at:', videoPlayer.currentTime);
        sendVideoProgress(videoPlayer.currentTime);
    });

    videoPlayer.addEventListener('ended', () => {
        console.log('Video ended at:', videoPlayer.currentTime);
        sendVideoProgress(videoPlayer.currentTime);
    });
    window.addEventListener('beforeunload', () => {
        console.log('Page is unloading, sending progress...');
        sendVideoProgress(videoPlayer.currentTime);
    });
}




function getCSRFToken(): string | null {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [key, value] = cookie.trim().split('=');
        if (key === name) {
            return decodeURIComponent(value);
        }
    }
    return null;
}