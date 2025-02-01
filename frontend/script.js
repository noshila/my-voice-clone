document.addEventListener('DOMContentLoaded', () => {
    const promptAudioInput = document.getElementById('promptAudio');
    const targetTextInput = document.getElementById('targetText');
    const generateButton = document.getElementById('generateButton');
    const audioPlayer = document.getElementById('audioPlayer');
    const waveformContainer = document.getElementById('waveform');
    const downloadLink = document.getElementById('downloadLink');
    const statusDiv = document.getElementById('status');

    let wavesurfer = WaveSurfer.create({
        container: waveformContainer,
        waveColor: 'violet',
        progressColor: 'purple',
        cursorColor: 'navy',
        barWidth: 2,
        height: 80,
        responsive: true,
        hideScrollbar: true,
        interact: true,
    });

    generateButton.addEventListener('click', async () => {
        statusDiv.textContent = 'Generating speech...';
        generateButton.disabled = true;
        downloadLink.style.display = 'none';
        waveformContainer.innerHTML = ''; // Clear previous waveform
        wavesurfer.destroy(); // Destroy previous instance
        wavesurfer = WaveSurfer.create({ // Re-initialize
            container: waveformContainer,
            waveColor: 'violet',
            progressColor: 'purple',
            cursorColor: 'navy',
            barWidth: 2,
            height: 80,
            responsive: true,
            hideScrollbar: true,
            interact: true,
        });

        const text = targetTextInput.value;
        const audioFile = promptAudioInput.files[0];

        if (!text || !audioFile) {
            statusDiv.textContent = 'Please provide both text and a voice prompt.';
            generateButton.disabled = false;
            return;
        }

        const formData = new FormData();
        formData.append('target_text', text);
        formData.append('prompt_audio_file', audioFile);

        try {
            const response = await fetch('/clone_voice/', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                statusDiv.textContent = `Error: ${errorData.error || 'Failed to generate speech.'}`;
            } else {
                const data = await response.json();
                audioPlayer.src = data.audio_url;
                wavesurfer.load(data.audio_url);
                downloadLink.href = data.audio_url;
                downloadLink.download = 'generated_voice.wav';
                downloadLink.style.display = 'block';
                statusDiv.textContent = 'Speech generated successfully!';
            }
        } catch (error) {
            console.error('Fetch error:', error);
            statusDiv.textContent = 'Error generating speech. Please check console.';
        } finally {
            generateButton.disabled = false;
        }
    });
});
