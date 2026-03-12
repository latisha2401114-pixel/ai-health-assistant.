// ================= DOM =================
const conversation = document.getElementById("conversation");
const status = document.getElementById("status");
const micBtn = document.getElementById("micBtn");
const emergencyBtn = document.getElementById("emergencyBtn");

if (!conversation || !status || !micBtn) {
    console.error("Required DOM elements missing");
}

// ================= CHECK BROWSER SUPPORT =================
if (!("speechSynthesis" in window)) {
    alert("Speech Synthesis not supported. Use Chrome.");
}

// ================= SPEECH RECOGNITION INIT =================
let recognition = null;

if ("webkitSpeechRecognition" in window) {
    recognition = new webkitSpeechRecognition();
} else if ("SpeechRecognition" in window) {
    recognition = new SpeechRecognition();
} else {
    alert("Speech Recognition not supported. Use Chrome.");
}

// ================= MESSAGES =================
const MSG = {
    ta: {
        askLang: "நீங்கள் எந்த மொழியில் பேச விரும்புகிறீர்கள்? தமிழ் அல்லது ஆங்கிலம்?",
        greeting: "வணக்கம்! நான் உங்கள் AI மருத்துவ உதவியாளர். என்ன உதவி வேண்டும்?",
        askName: "உங்கள் பெயரை சொல்லுங்கள்",
        askSymptoms: "உங்கள் அறிகுறிகளை சொல்லுங்கள்",
        askTime: "நேரம் சொல்லுங்கள். உதாரணம் 10 மணி",
        askPhone: "உங்கள் 10 இலக்க மொபைல் நம்பர் சொல்லுங்கள்",
        invalidTime: "சரியான நேரம் சொல்லுங்கள்",
        invalidPhone: "சரியான 10 இலக்க நம்பர் சொல்லுங்கள்",
        booked: "உங்கள் டாக்டர் சந்திப்பு வெற்றிகரமாக பதிவு செய்யப்பட்டது. நன்றி.",
        emergency: "உடனடியாக அருகிலுள்ள மருத்துவமனைக்கு செல்லவும்"
    },
    en: {
        askLang: "Which language do you prefer? Tamil or English?",
        greeting: "Hello! I am your AI medical assistant. How can I help you?",
        askName: "Please tell your name",
        askSymptoms: "Please tell your symptoms",
        askTime: "Tell the time. Example 10",
        askPhone: "Please say your 10 digit mobile number",
        invalidTime: "Please say a valid time",
        invalidPhone: "Please say a valid 10 digit number",
        booked: "Your doctor appointment has been booked successfully. Thank you.",
        emergency: "Please go to the nearest hospital immediately"
    }
};

// ================= STATE =================
let step = "ASK_LANGUAGE";
let currentLang = "en";
let recognizing = false;
let conversationEnded = false;
let aiStarted = false;
let appointmentTime = "";   // ⭐ store spoken time
let patientName = "";
let patientSymptoms = "";
// ================= SPEAK =================
function speak(text, lang = currentLang) {

    window.speechSynthesis.cancel();

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = (lang === "ta") ? "ta-IN" : "en-IN";
    utter.rate = 0.9;

    conversation.innerHTML += `<p><b>AI:</b> ${text}</p>`;
    status.innerText = "🗣 Speaking...";

    utter.onend = () => {
        if (!conversationEnded) {
            status.innerText = "🎤 Listening...";
            setTimeout(() => {
                startListening();
            }, 500);
        } else {
            status.innerText = "✅ Completed";
        }
    };

    speechSynthesis.speak(utter);
}

// ================= LISTEN =================
function startListening() {

    if (!recognition || speechSynthesis.speaking) return;

    try { recognition.stop(); } catch (e) {}

    recognizing = true;
    recognition.lang = (currentLang === "ta") ? "ta-IN" : "en-IN";
    status.innerText = "🎤 Listening...";
    recognition.start();
}

// ================= RECOGNITION =================
if (recognition) {

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = "";

    recognition.onresult = (event) => {

        let interimTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {

            const transcript = event.results[i][0].transcript;

            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        status.innerText = "🎤 Listening: " + interimTranscript;

        if (finalTranscript !== "") {

            const text = finalTranscript.trim().toLowerCase();

            conversation.innerHTML += `<p><b>Patient:</b> ${text}</p>`;

            finalTranscript = "";
            recognizing = false;

            processAI(text);
        }
    };

    recognition.onerror = (event) => {
        recognizing = false;
        status.innerText = "❌ Voice error: " + event.error;
    };

    recognition.onend = () => {

        recognizing = false;

        if (!conversationEnded && !speechSynthesis.speaking) {
            setTimeout(() => {
                startListening();
            }, 700);
        }
    };
}

// ================= AI LOGIC =================
function processAI(text) {

    if (text.includes("emergency") || text.includes("அவசரம்")) {
        speak(MSG[currentLang].emergency);
        conversationEnded = true;
        return;
    }

    if (step === "ASK_LANGUAGE") {

        if (text.includes("tamil") || text.includes("தமிழ்")) {
            currentLang = "ta";
            step = "ASK_PURPOSE";
            speak(MSG.ta.greeting, "ta");
            return;
        }

        if (text.includes("english")) {
            currentLang = "en";
            step = "ASK_PURPOSE";
            speak(MSG.en.greeting, "en");
            return;
        }

        speak(MSG.en.askLang);
        return;
    }

    if (step === "ASK_PURPOSE") {
    step = "ASK_NAME";
    speak(MSG[currentLang].askName);
    return;
    }
    
     if (step === "ASK_NAME") {

    patientName = text;

    step = "ASK_SYMPTOMS";

    speak(MSG[currentLang].askSymptoms);

    return;
}
   if (step === "ASK_SYMPTOMS") {

    patientSymptoms = text;

    step = "ASK_TIME";

    speak(MSG[currentLang].askTime);

    return;
}

    // ⭐ TIME CAPTURE FIX
    if (step === "ASK_TIME") {

        const match = text.match(/\d+/);

        if (!match) {
            speak(MSG[currentLang].invalidTime);
            return;
        }

        appointmentTime = match[0] + ":00";   // store user time
        step = "ASK_PHONE";

        speak(MSG[currentLang].askPhone);
        return;
    }

    if (step === "ASK_PHONE") {

        const digits = text.replace(/\D/g, "");

        if (digits.length !== 10) {
            speak(MSG[currentLang].invalidPhone);
            return;
        }

        fetch("/book_appointments_multi", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
           body: JSON.stringify({
    name: patientName,
    symptoms: patientSymptoms,
    time: appointmentTime,
    phone: digits
})
        })
        .then(res => res.json())
        .then(data => {
            speak(MSG[currentLang].booked);
            conversationEnded = true;
        })
        .catch(err => {
            console.error(err);
            speak("Appointment booking failed");
        });
    }
}

// ================= MIC BUTTON =================
micBtn.onclick = () => {

    if (aiStarted) return;

    aiStarted = true;
    conversation.innerHTML = "";
    conversationEnded = false;
    step = "ASK_LANGUAGE";

    speak(MSG.en.askLang);
};

// ================= EMERGENCY =================
if (emergencyBtn) {
    emergencyBtn.onclick = () => {
        window.location.href = "tel:108";
    };
}

// ================= UI NAVIGATION =================
function hideAllSections() {
    document.getElementById("dashboardSection").style.display = "none";
    document.getElementById("appointmentsSection").style.display = "none";
    document.getElementById("prescriptionsSection").style.display = "none";
}

function showDashboard() {
    hideAllSections();
    document.getElementById("dashboardSection").style.display = "block";
}

function showAppointments() {
    hideAllSections();
    document.getElementById("appointmentsSection").style.display = "block";
}

function showPrescriptions() {
    hideAllSections();
    document.getElementById("prescriptionsSection").style.display = "block";
}