let socket;
let recorder;
let isRecording = false;

const channelId = generateUUID();
const host_url = "7011-61-12-85-170.ngrok-free.app"

const generateOfferButton = document.getElementById('generateOfferButton');
const question = document.getElementById('question');
const user_response = document.getElementById('user_response');
const status = document.getElementById('status');
const error_message = document.getElementById('error_message');
const termination_message = document.getElementById('termination_message');
const audioPlayer = document.getElementById('audioPlayer');
const result_container = document.getElementById('result_container');

generateOfferButton.addEventListener('click', initializeWebSocket);

async function initializeWebSocket() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('Microphone permission granted');

        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        analyser.fftSize = 2048;
        dataArray = new Uint8Array(analyser.frequencyBinCount);

        socket = new WebSocket(`wss://${host_url}/ws/${channelId}`);

        socket.onopen = () => {
            console.log('WebSocket connection established');
            socket.send(JSON.stringify({ type: 'acknowledge', channelId: channelId }));
            generateOfferButton.disabled = true;
        };

        socket.onmessage = handleSocketMessage;

        socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            status.textContent = `WebSocket Error: ${error.message}`;
        };

        socket.onclose = () => {
            console.log('WebSocket connection closed');
            generateOfferButton.disabled = false;
        };
    } catch (error) {
        console.error('Error accessing microphone:', error);
        status.textContent = 'Microphone permission denied or error occurred. WebSocket not initialized.';
        return;
    }
}

function displayResultJson(result_json) {
    result_container.innerHTML = '';
    const table = document.createElement('table');
    table.className = "table table-bordered table-sm";

    const header = document.createElement('tr');
    const headerKeyCell = document.createElement('th');
    const headerValueCell = document.createElement('th');

    headerKeyCell.textContent = "Car Attribute";
    headerValueCell.textContent = "Value";

    header.appendChild(headerKeyCell);
    header.appendChild(headerValueCell);
    table.appendChild(header);

    for (const key in result_json) {
        if (result_json[key]) {
            const row = document.createElement('tr');
            const keyCell = document.createElement('td');
            const valueCell = document.createElement('td');

            keyCell.textContent = key.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
            valueCell.textContent = result_json[key];

            row.appendChild(keyCell);
            row.appendChild(valueCell);
            table.appendChild(row);
        }
    }
    result_container.appendChild(table);
}

function updateUIElement(element, content, prefix = '') {
    if (content && content.trim() !== "") {
        element.style.display = 'block';
        element.textContent = prefix + content;
    } else {
        element.style.display = 'none';
    }
}

async function handleSocketMessage(event) {
    const message = JSON.parse(event.data);

    console.log(message);
    updateUIElement(user_response, message.user_response, "User Response: ")

    if (message.result_json && message.result_json.trim() !== "") {
        var result_json_data = JSON.parse(message.result_json)
        displayResultJson(result_json_data)
    }

    if (message.error && message.error.path) {
        status.style.display = 'none';
        if (message.error.path) {
            status.style.display = 'none';
            updateUIElement(error_message, message.error.message, "Error Message: ")
            console.error(message.error.message);
            await playAudio(message.error.path);
        }

        if (message.question && message.question.path && message.is_exiting != 'true') {
            error_message.style.display = 'none';
            updateUIElement(question, message.question.text, "Question: ")
            console.log("Question:", message.question.text);
            await playAudio(message.question.path);
        }
    }

    else if (message.initial_message_path) {
        status.style.display = 'none';
        await playAudio(message.initial_message_path);

        if (message.question && message.question.path) {
            error_message.style.display = 'none'
            updateUIElement(question, message.question.text, "Question: ")
            console.log("Question:", message.question.text);
            await playAudio(message.question.path);
        }
    }

    else if (message.question && message.question.path) {
        status.style.display = 'none';
        error_message.style.display = 'none';
        updateUIElement(question, message.question.text, "Question: ")
        console.log("Question:", message.question.text);
        await playAudio(message.question.path);
    }

    else if (message.terminate && message.terminate.message) {
        status.style.display = 'none';
        question.style.display = 'none';
        error_message.style.display = 'none';
        updateUIElement(termination_message, message.terminate.message)
        if (message.terminate.path) {
            status.style.display = 'none';
            await playAudio(message.terminate.path);
        }
        console.log("Termination message: ", message.terminate.message);
        return;
    }

    status.style.display = 'block';
    status.textContent = "Listening Audio...";
    await startRecording();
}

function playAudio(filepath) {
    status.style.display = 'none';
    return new Promise((resolve) => {
        audioPlayer.src = filepath;
        audioPlayer.onended = resolve;
        audioPlayer.play();
    });
}

async function startRecording() {
    if (isRecording) return;
    isRecording = true;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new RecordRTC(stream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: RecordRTC.StereoAudioRecorder,
        numberOfAudioChannels: 1,
        sampleRate: 44100,
        desiredSampRate: 16000
    });

    recorder.startRecording();
    monitorAudioLevels();
}


function monitorAudioLevels() {
    let silenceStart = null;
    const silenceThreshold = 10;
    const silenceDuration = 3000;

    function checkAudioLevel() {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;

        if (average > silenceThreshold) {
            silenceStart = null;
        } else if (!silenceStart) {
            silenceStart = Date.now();
        }

        if (silenceStart && Date.now() - silenceStart > silenceDuration) {
            stopRecordingAndSend();
        } else if (isRecording) {
            requestAnimationFrame(checkAudioLevel);
        }
    }

    checkAudioLevel();
}

function stopRecordingAndSend() {
    if (!isRecording) return;
    isRecording = false;

    recorder.stopRecording(() => {
        const blob = recorder.getBlob();
        sendAudioToServer(blob);
    });
}

function sendAudioToServer(blob) {
    const reader = new FileReader();
    reader.onload = () => {
        const arrayBuffer = reader.result;
        socket.send(arrayBuffer);
        status.textContent = "Audio sent, Waiting for response...";
    };
    reader.readAsArrayBuffer(blob);
}

function generateUUID() {
    var d = new Date().getTime();
    var d2 = (performance && performance.now && (performance.now()*1000)) || 0;
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16;
        if (d > 0) {
            r = (d + r) % 16 | 0;
            d = Math.floor(d / 16);
        } else {
            r = (d2 + r) % 16 | 0;
            d2 = Math.floor(d2 / 16);
        }
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}