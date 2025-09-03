let currentTaskId = null;
let pollInterval = null;

document.getElementById("downloadForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);

    const payload = {
        channel_url: formData.get("channelUrl"),
        quality: formData.get("quality"),
        max_videos: parseInt(formData.get("maxVideos")) || 10,
        audio_only: formData.has("audioOnly")
    };

    const progressLog = document.getElementById("progressLog");
    const downloadSection = document.getElementById("downloadSection");
    
    progressLog.textContent = "Submitting download task...";
    downloadSection.style.display = "none";

    try {
        const res = await fetch("/api/download_enhanced", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error("Failed to start task");
        }

        const data = await res.json();
        currentTaskId = data.task_id;

        progressLog.textContent = `Task started (ID: ${currentTaskId}). Polling progress...\n`;

        // Clear any existing interval
        if (pollInterval) {
            clearInterval(pollInterval);
        }

        // Poll progress every 2 seconds
        pollInterval = setInterval(async () => {
            try {
                const progressRes = await fetch(`/api/progress/${currentTaskId}`);
                if (progressRes.ok) {
                    const progressData = await progressRes.json();
                    progressLog.textContent = progressData.progress;

                    // Check if download is complete
                    if (progressData.progress.includes("All downloads finished") || 
                        progressData.progress.includes("Task completed")) {
                        clearInterval(pollInterval);
                        showDownloadSection();
                    } else if (progressData.progress.includes("error") || 
                               progressData.progress.includes("failed")) {
                        clearInterval(pollInterval);
                    }
                } else {
                    console.error("Failed to fetch progress");
                }
            } catch (err) {
                console.error("Error polling progress:", err);
            }
        }, 2000);

    } catch (err) {
        progressLog.textContent = "Error: " + err.message;
    }
});

function showDownloadSection() {
    const downloadSection = document.getElementById("downloadSection");
    downloadSection.style.display = "block";
    
    // Setup ZIP download button
    const zipBtn = document.getElementById("downloadZip");
    zipBtn.onclick = () => {
        if (currentTaskId) {
            window.open(`/api/zip/${currentTaskId}`, '_blank');
        }
    };
}
