// ==============================
// MEMORA - START LEARNING
// ==============================

const startButton = document.querySelector(".start-btn");

startButton.addEventListener("click", function () {
    document.querySelector(".features").scrollIntoView({
        behavior: "smooth"
    });
});


// ==============================
// MEMORA - STUDY MODES
// ==============================

const modeButtons = document.querySelectorAll(".mode-btn");

let selectedMode = "explain";

modeButtons.forEach(function (button) {

    button.addEventListener("click", function () {

        modeButtons.forEach(function (btn) {
            btn.classList.remove("active");
        });

        button.classList.add("active");

        selectedMode = button.dataset.mode;

        console.log("Selected mode:", selectedMode);
    });

});


// ==============================
// MEMORA - GENERATE AI RESULT
// ==============================

const generateButton = document.querySelector(".generate-btn");
const studyInput = document.querySelector("#studyInput");
const outputContent = document.querySelector(".output-content");

generateButton.addEventListener("click", async function () {

    const userInput = studyInput.value.trim();

    // Check empty input
    if (userInput === "") {

        outputContent.innerHTML = `
            <div class="output-icon">⚠️</div>
            <h3>Please enter something first</h3>
            <p>
                Enter a topic, question, notes, or your answer
                before generating a result.
            </p>
        `;

        return;
    }


    // Loading message
    outputContent.innerHTML = `
        <div class="output-icon">⏳</div>
        <h3>MEMORA is thinking...</h3>
        <p>Creating your learning result.</p>
    `;


    try {

        const response = await fetch(
            "/api/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    input: userInput,
                    mode: selectedMode
                })
            }
        );


        const data = await response.json();


        // API ERROR
if (!response.ok) {

    if (response.status === 429) {

        outputContent.innerHTML = `
            <div class="output-icon">⏳</div>
            <h3>AI LIMIT REACHED</h3>
            <p>
                MEMORA has reached today's AI request limit.
            </p>
            <p>
                Please try again later when the AI limit resets.
            </p>
        `;

    } else {

        outputContent.innerHTML = `
            <div class="output-icon">⚠️</div>
            <h3>MEMORA ERROR</h3>
            <p>
                ${data.error || "Something went wrong."}
            </p>
        `;
    }

    return;
}


        // SUCCESS
        outputContent.innerHTML = `
            <div class="output-icon">🤖</div>

            <h3>MEMORA'S RESPONSE</h3>

            <div class="ai-response">
                ${marked.parse(data.result)}
            </div>
        `;


    } catch (error) {

        outputContent.innerHTML = `
            <div class="output-icon">⚠️</div>

            <h3>MEMORA needs a moment</h3>

            <p>
                We couldn't generate your learning result.
                Please check your connection and try again.
            </p>
        `;

        console.error("MEMORA ERROR:", error);
    }

});


// ==============================
// MEMORA - STUDY PLANNER
// ==============================

const plannerButton = document.querySelector(".planner-btn");

const examName = document.querySelector("#examName");
const examDate = document.querySelector("#examDate");
const subjects = document.querySelector("#subjects");
const studyHours = document.querySelector("#studyHours");

const plannerResult = document.querySelector(".planner-result");


plannerButton.addEventListener("click", function () {

    // Get values
    const name = examName.value.trim();
    const date = examDate.value;
    const subjectText = subjects.value.trim();
    const hours = studyHours.value;


    // ==============================
    // VALIDATION
    // ==============================

    if (
        name === "" ||
        date === "" ||
        subjectText === "" ||
        hours === ""
    ) {

        plannerResult.innerHTML = `
            <div class="output-icon">⚠️</div>

            <h3>Please fill all details</h3>

            <p>
                Enter your exam name, exam date,
                subjects and daily study time.
            </p>
        `;

        return;
    }


    // ==============================
    // CALCULATE DAYS
    // ==============================

    const today = new Date();

    today.setHours(0, 0, 0, 0);

    const exam = new Date(date);

    exam.setHours(0, 0, 0, 0);


    const difference =
        exam.getTime() - today.getTime();

    const daysLeft =
        Math.ceil(
            difference / (1000 * 60 * 60 * 24)
        );


    // Check past date
    if (daysLeft < 1) {

        plannerResult.innerHTML = `
            <div class="output-icon">⚠️</div>

            <h3>Choose a future exam date</h3>

            <p>
                Your exam date should be at least
                one day from today.
            </p>
        `;

        return;
    }


    // ==============================
    // GET SUBJECTS
    // ==============================

    const subjectList = subjectText
        .split("\n")
        .map(function (subject) {
            return subject.trim();
        })
        .filter(function (subject) {
            return subject !== "";
        });


    if (subjectList.length === 0) {

        plannerResult.innerHTML = `
            <div class="output-icon">⚠️</div>

            <h3>Please enter your subjects</h3>

            <p>
                Add at least one subject to create
                your study plan.
            </p>
        `;

        return;
    }


    // ==============================
    // CREATE BASIC PLAN
    // ==============================

    let planHTML = `
        <div class="output-icon">📚</div>

        <h3>${name}</h3>

        <p>
            You have <strong>${daysLeft} days</strong>
            remaining.
        </p>

        <p>
            Daily study time:
            <strong>${hours} hour(s)</strong>
        </p>

        <hr>

        <h3>📅 Your Study Plan</h3>
    `;


    // Create subject schedule
    subjectList.forEach(function (subject, index) {

        const dayNumber =
            (index % daysLeft) + 1;

        planHTML += `
            <p>
                <strong>Day ${dayNumber}:</strong>
                ${subject}
            </p>
        `;

    });


    planHTML += `
        <hr>

        <p>
            💡 <strong>MEMORA Tip:</strong>
            Study actively, take short breaks,
            and revise important topics regularly.
        </p>
    `;


    // Show plan
    plannerResult.innerHTML = planHTML;

});
// ==============================
// MEMORA - POMODORO TIMER
// ==============================

const timerDisplay = document.querySelector("#timerDisplay");
const timerMode = document.querySelector("#timerMode");
const timerMessage = document.querySelector("#timerMessage");

const startTimerButton = document.querySelector("#startTimer");
const pauseTimerButton = document.querySelector("#pauseTimer");
const resetTimerButton = document.querySelector("#resetTimer");

const timerOptions = document.querySelectorAll(".timer-option");


// Default timer
let focusMinutes = 25;
let breakMinutes = 5;

let timeLeft = focusMinutes * 60;

let timerInterval = null;

let isFocusTime = true;


// ==============================
// DISPLAY TIMER
// ==============================

function updateTimerDisplay() {

    const minutes = Math.floor(timeLeft / 60);

    const seconds = timeLeft % 60;

    timerDisplay.textContent =
        String(minutes).padStart(2, "0") +
        ":" +
        String(seconds).padStart(2, "0");
}


// Show initial timer
updateTimerDisplay();


// ==============================
// TIMER OPTIONS
// ==============================

timerOptions.forEach(function (button) {

    button.addEventListener("click", function () {

        // Stop current timer
        clearInterval(timerInterval);

        timerInterval = null;

        // Remove active
        timerOptions.forEach(function (btn) {
            btn.classList.remove("active");
        });

        // Add active
        button.classList.add("active");

        // Get selected times
        focusMinutes =
            Number(button.dataset.focus);

        breakMinutes =
            Number(button.dataset.break);

        // Reset to focus time
        isFocusTime = true;

        timeLeft = focusMinutes * 60;

        timerMode.textContent = "FOCUS TIME";

        timerMessage.textContent =
            "Time to focus on your studies.";

        updateTimerDisplay();

    });

});


// ==============================
// START TIMER
// ==============================

startTimerButton.addEventListener("click", function () {

    // Prevent multiple timers
    if (timerInterval !== null) {
        return;
    }

    timerInterval = setInterval(function () {

        timeLeft--;

        updateTimerDisplay();


        // Timer finished
        if (timeLeft <= 0) {

            clearInterval(timerInterval);

            timerInterval = null;


            // Focus finished
            if (isFocusTime) {

                isFocusTime = false;

                timeLeft = breakMinutes * 60;

                timerMode.textContent =
                    "BREAK TIME";

                timerMessage.textContent =
                    "Great job! Take a short break. ☕";

            }


            // Break finished
            else {

                isFocusTime = true;

                timeLeft = focusMinutes * 60;

                timerMode.textContent =
                    "FOCUS TIME";

                timerMessage.textContent =
                    "Break finished. Ready to study again? 📚";

            }

            updateTimerDisplay();
        }

    }, 1000);

});


// ==============================
// PAUSE TIMER
// ==============================

pauseTimerButton.addEventListener("click", function () {

    clearInterval(timerInterval);

    timerInterval = null;

    timerMessage.textContent =
        "Timer paused. Continue whenever you're ready.";

});


// ==============================
// RESET TIMER
// ==============================

resetTimerButton.addEventListener("click", function () {

    clearInterval(timerInterval);

    timerInterval = null;

    isFocusTime = true;

    timeLeft = focusMinutes * 60;

    timerMode.textContent =
        "FOCUS TIME";

    timerMessage.textContent =
        "Time to focus on your studies.";

    updateTimerDisplay();

});
// ==============================
// MEMORA - QUICK STUDY
// ==============================

const quickTopic = document.querySelector("#quickTopic");

const quickTimeButtons =
    document.querySelectorAll(".quick-time");

const quickStudyButton =
    document.querySelector(".quick-study-btn");

const quickResult =
    document.querySelector(".quick-result");

let selectedQuickTime = 5;


// ==============================
// SELECT STUDY TIME
// ==============================

quickTimeButtons.forEach(function (button) {

    button.addEventListener("click", function () {

        // Remove active from all
        quickTimeButtons.forEach(function (btn) {
            btn.classList.remove("active");
        });

        // Add active to selected button
        button.classList.add("active");

        // Store selected time
        selectedQuickTime =
            Number(button.dataset.minutes);

        console.log(
            "Quick Study Time:",
            selectedQuickTime,
            "minutes"
        );

    });

});


// ==============================
// START QUICK STUDY
// ==============================

quickStudyButton.addEventListener("click", function () {

    const topic = quickTopic.value.trim();


    // ==============================
    // EMPTY INPUT CHECK
    // ==============================

    if (topic === "") {

        quickResult.innerHTML = `
            <div class="output-icon">⚠️</div>

            <h3>Enter a topic first</h3>

            <p>
                Tell MEMORA what you want to study
                before starting your quick session.
            </p>
        `;

        return;
    }


    // ==============================
    // CREATE QUICK SESSION
    // ==============================

    quickResult.innerHTML = `

        <div class="output-icon">⚡</div>

        <h3>${selectedQuickTime}-Minute Study Session</h3>

        <p>
            Let's study:
            <strong>${topic}</strong>
        </p>

        <hr>

        <div class="ai-response">

            <h3>🧠 1. Learn</h3>

            <p>
                Spend the first part of your session
                understanding the basic idea of
                <strong>${topic}</strong>.
            </p>


            <h3>💡 2. Understand</h3>

            <p>
                Think about one simple example
                related to the topic.
            </p>


            <h3>✍️ 3. Practice</h3>

            <p>
                Try explaining the topic in your
                own words or solve one small problem.
            </p>


            <h3>🧠 4. Recall</h3>

            <p>
                Close your notes and remember
                the three most important points.
            </p>


            <hr>

            <p>
                ⏱️ You have
                <strong>${selectedQuickTime} minutes</strong>.
            </p>

            <p>
                🍅 Tip: Start the Pomodoro timer above
                and stay focused until your session ends.
            </p>

        </div>
    `;

});
// ==========================================
// TEACH IT BACK
// ==========================================

const teachTopic = document.querySelector("#teachTopic");
const teachAnswer = document.querySelector("#teachAnswer");
const teachBackButton = document.querySelector(".teach-back-btn");
const teachResult = document.querySelector(".teach-result");

teachBackButton.addEventListener("click", async function () {

    const topic = teachTopic.value.trim();
    const answer = teachAnswer.value.trim();

    // Check empty topic
    if (topic === "") {
        teachResult.innerHTML = `
            <div class="output-icon">⚠️</div>
            <h3>Enter a topic first</h3>
            <p>Please tell MEMORA what topic you are explaining.</p>
        `;
        return;
    }

    // Check empty answer
    if (answer === "") {
        teachResult.innerHTML = `
            <div class="output-icon">⚠️</div>
            <h3>Explain the topic first</h3>
            <p>Write your explanation in your own words and then ask MEMORA to check it.</p>
        `;
        return;
    }

    // Show loading
    teachResult.innerHTML = `
        <div class="output-icon">🧠</div>
        <h3>MEMORA is checking your understanding...</h3>
        <p>Please wait.</p>
    `;

    try {

        // Send topic + answer to Flask
        const response = await fetch(
            "/api/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    input: `
Topic: ${topic}

Student's explanation:
${answer}
                    `,
                    mode: "teach"
                })
            }
        );

        const data = await response.json();

        // API error
        if (!response.ok) {

            if (response.status === 429) {

                teachResult.innerHTML = `
                    <div class="output-icon">⏳</div>
                    <h3>AI LIMIT REACHED</h3>
                    <p>
                        MEMORA has reached today's AI request limit.
                    </p>
                    <p>
                        Please try again later when the AI limit resets.
                    </p>
                `;

            } else {

                teachResult.innerHTML = `
                    <div class="output-icon">⚠️</div>
                    <h3>MEMORA ERROR</h3>
                    <p>
                        ${data.error || "Something went wrong."}
                    </p>
                `;
            }

            return;
        }

        // Show AI result
        teachResult.innerHTML = `
            <div class="ai-response">
                ${marked.parse(data.result)}
            </div>
        `;

    } catch (error) {

        console.error(error);

        teachResult.innerHTML = `
            <div class="output-icon">⚠️</div>
            <h3>Connection Error</h3>
            <p>
                MEMORA could not connect to the AI server.
                Please make sure the Flask server is running.
            </p>
        `;
    }

});
// ==========================================
// UPLOAD & STUDY 📎📚
// ==========================================

const studyFile = document.querySelector("#studyFile");
const selectedFile = document.querySelector("#selectedFile");

studyFile.addEventListener("change", function () {

    const file = studyFile.files[0];

    if (!file) {
        selectedFile.innerHTML = `
            <span>📄</span>
            <span>No file selected yet</span>
        `;
        return;
    }

    selectedFile.innerHTML = `
    <div class="file-info">
        <span class="file-icon">📚</span>

        <div>
            <strong>${file.name}</strong>
            <small>Ready to study</small>
        </div>
    </div>
`;
document.querySelector("#documentActions").style.display = "block";

    // IMAGE
    if (file.type.startsWith("image/")) {

        const imageURL = URL.createObjectURL(file);

        selectedFile.innerHTML += `
            <div class="image-preview">
                <img src="${imageURL}" alt="Selected study image">
            </div>

            <button class="study-file-btn" id="studyFileButton">
                ✦ Study This Image
            </button>
        `;
    }

    // PDF
    else if (file.type === "application/pdf") {

        selectedFile.innerHTML += `
            <div class="file-message">
                <p>📄 PDF selected successfully!</p>

                <button class="study-file-btn" id="studyPdfButton">
                    ✦ Study This PDF
                </button>
            </div>
        `;
    }

    // POWERPOINT
    else if (
        file.type === "application/vnd.ms-powerpoint" ||
        file.type === "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ) {

        selectedFile.innerHTML += `
            <div class="file-message">
                <p>📊 Presentation selected successfully!</p>

                <button class="study-file-btn" id="studyPptButton">
                    ✦ Study This Presentation
                </button>
            </div>
        `;
    }

    // TEXT FILE
    else if (file.type === "text/plain") {

        selectedFile.innerHTML += `
            <div class="file-message">
                <p>📝 Text file selected successfully!</p>

                <button class="study-file-btn" id="studyTxtButton">
                    ✦ Study This Text
                </button>
            </div>
        `;
    }

});
// ==========================================
// STUDY THIS IMAGE 🖼️🧠
// ==========================================

document.addEventListener("click", async function (event) {

    if (event.target.id !== "studyFileButton") {
        return;
    }

    const file = studyFile.files[0];

    if (!file) {
        return;
    }

    const button = event.target;

    button.textContent = "🧠 MEMORA is studying...";
    button.disabled = true;

    const formData = new FormData();

    formData.append("image", file);

    try {

        const response = await fetch(
            "/api/study-image",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {

            if (response.status === 429) {

                selectedFile.innerHTML += `
                    <div class="ai-response">
                        <h3>⏳ AI LIMIT REACHED</h3>
                        <p>
                            MEMORA has reached today's AI request limit.
                            Please try again later.
                        </p>
                    </div>
                `;

            } else {

                selectedFile.innerHTML += `
                    <div class="ai-response">
                        <h3>⚠️ MEMORA ERROR</h3>
                        <p>
                            ${data.error || "Something went wrong."}
                        </p>
                    </div>
                `;
            }

            button.textContent = "✦ Study This Image";
            button.disabled = false;

            return;
        }

        // Show AI result
        selectedFile.innerHTML += `
            <div class="ai-response image-ai-result">
                ${marked.parse(data.result)}
            </div>
        `;

        button.textContent = "✨ Studied by MEMORA";
        button.disabled = true;

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>
                <p>
                    MEMORA could not connect to the AI server.
                </p>
            </div>
        `;

        button.textContent = "✦ Study This Image";
        button.disabled = false;
    }

});
// ==========================================
// STUDY THIS PDF 📄🧠
// ==========================================

document.addEventListener("click", async function (event) {

    if (event.target.id !== "studyPdfButton") {
        return;
    }

    const file = studyFile.files[0];

    if (!file) {
        return;
    }

    const button = event.target;

    button.textContent = "📖 MEMORA is reading...";
    button.disabled = true;

    const formData = new FormData();

    formData.append("file", file);

    try {

        const response = await fetch(
            "/api/study-pdf",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {

            selectedFile.innerHTML += `
                <div class="ai-response">
                    <h3>⚠️ MEMORA ERROR</h3>
                    <p>
                        ${data.error || "Could not read the PDF."}
                    </p>
                </div>
            `;

            button.textContent = "✦ Study This PDF";
            button.disabled = false;

            return;
        }

        selectedFile.innerHTML += `
            <div class="ai-response image-ai-result">
                <h3>📚 PDF Text Extracted Successfully!</h3>
                <p>
                    MEMORA successfully read the text from your PDF.
                </p>

                <details>
                    <summary>View extracted text</summary>
                    <p>${data.result}</p>
                </details>
            </div>
        `;

        button.textContent = "✅ PDF Read Successfully";
        button.disabled = true;

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>
                <p>
                    MEMORA could not connect to the PDF server.
                </p>
            </div>
        `;

        button.textContent = "✦ Study This PDF";
        button.disabled = false;
    }

});
// ==========================================
// STUDY POWERPOINT 📊🧠
// ==========================================

document.addEventListener("click", async function (event) {

    if (event.target.id !== "studyPptButton") {
        return;
    }

    const file = studyFile.files[0];

    if (!file) {
        return;
    }

    const button = event.target;

    button.textContent = "📖 MEMORA is reading...";
    button.disabled = true;

    const formData = new FormData();

    formData.append("file", file);

    try {

        const response = await fetch(
            /api/study-ppt",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {

            selectedFile.innerHTML += `
                <div class="ai-response">
                    <h3>⚠️ MEMORA ERROR</h3>
                    <p>
                        ${data.error || "Could not read the presentation."}
                    </p>
                </div>
            `;

            button.textContent = "✦ Study This Presentation";
            button.disabled = false;

            return;
        }

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>📊 Presentation Text Extracted Successfully!</h3>

                <p>
                    MEMORA successfully read the text from your presentation.
                </p>

                <details>
                    <summary>View extracted slide text</summary>
                    <p>${data.result}</p>
                </details>
            </div>
        `;

        button.textContent = "✅ Presentation Read Successfully";
        button.disabled = true;

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>

                <p>
                    MEMORA could not connect to the presentation server.
                </p>
            </div>
        `;

        button.textContent = "✦ Study This Presentation";
        button.disabled = false;
    }
    uploadedStudyText = data.result;

});
// ==========================================
// STUDY TEXT FILE 📝🧠
// ==========================================

document.addEventListener("click", async function (event) {

    if (event.target.id !== "studyTxtButton") {
        return;
    }

    const file = studyFile.files[0];

    if (!file) {
        return;
    }

    const button = event.target;

    button.textContent = "📖 MEMORA is reading...";
    button.disabled = true;

    const formData = new FormData();
    formData.append("file", file);

    try {

        const response = await fetch(
            "/api/study-txt",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();
        uploadedStudyText = data.result;
        

        if (!response.ok) {

            selectedFile.innerHTML += `
                <div class="ai-response">
                    <h3>⚠️ MEMORA ERROR</h3>
                    <p>${data.error || "Could not read the text file."}</p>
                </div>
            `;

            button.textContent = "✦ Study This Text";
            button.disabled = false;
            return;
        }
        uploadedStudyText = data.result;

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>📝 Text File Read Successfully!</h3>

                <p>
                    MEMORA successfully read your text file.
                </p>

                <details>
                    <summary>View extracted text</summary>
                    <p>${data.result}</p>
                </details>
            </div>
        `;

        button.textContent = "✅ Text Read Successfully";
        button.disabled = true;

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>

                <p>
                    MEMORA could not connect to the text file server.
                </p>
            </div>
        `;

        button.textContent = "✦ Study This Text";
        button.disabled = false;
    }

});
// ==========================================
// DOCUMENT AI — SUMMARIZE ✨
// ==========================================

document.addEventListener("click", async function (event) {

    if (!event.target.classList.contains("document-action-btn")) {
        return;
    }

    const action = event.target.textContent.trim();

    // Only handle Summarize for now
    if (!action.includes("Summarize")) {
        return;
    }

    if (!uploadedStudyText.trim()) {

        alert("Please upload and read a study file first.");

        return;
    }

    const button = event.target;

    button.textContent = "🧠 MEMORA is thinking...";
    button.disabled = true;

    try {

        const response = await fetch(
            "/api/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    input: uploadedStudyText,

                    mode: "summarize"

                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            selectedFile.innerHTML += `
                <div class="ai-response">
                    <h3>⚠️ MEMORA ERROR</h3>
                    <p>${data.error || "Something went wrong."}</p>
                </div>
            `;

            button.textContent = "✨ Summarize";
            button.disabled = false;

            return;
        }

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>✨ MEMORA Summary</h3>

                ${marked.parse(data.result)}
            </div>
        `;

        button.textContent = "✅ Summarized";

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>

                <p>
                    MEMORA could not connect to the AI server.
                </p>
            </div>
        `;

        button.textContent = "✨ Summarize";
        button.disabled = false;
    }

});
// ==========================================
// DOCUMENT AI — EXPLAIN SIMPLY 🧠
// ==========================================

document.addEventListener("click", async function (event) {

    if (!event.target.classList.contains("document-action-btn")) {
        return;
    }

    const action = event.target.textContent.trim();

    // Only handle Explain Simply
    if (!action.includes("Explain Simply")) {
        return;
    }

    if (!uploadedStudyText.trim()) {

        alert("Please upload and read a study file first.");

        return;
    }

    const button = event.target;

    button.textContent = "🧠 MEMORA is thinking...";
    button.disabled = true;

    try {

        const response = await fetch(
            "/api/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    input: uploadedStudyText,

                    mode: "simple"

                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            selectedFile.innerHTML += `
                <div class="ai-response">
                    <h3>⚠️ MEMORA ERROR</h3>
                    <p>${data.error || "Something went wrong."}</p>
                </div>
            `;

            button.textContent = "🧠 Explain Simply";
            button.disabled = false;

            return;
        }

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>🧠 MEMORA's Simple Explanation</h3>

                ${marked.parse(data.result)}
            </div>
        `;

        button.textContent = "✅ Explained";

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>

                <p>
                    MEMORA could not connect to the AI server.
                </p>
            </div>
        `;

        button.textContent = "🧠 Explain Simply";
        button.disabled = false;
    }

});
// ==========================================
// DOCUMENT AI — IMPORTANT POINTS ⭐
// ==========================================

document.addEventListener("click", async function (event) {

    if (!event.target.classList.contains("document-action-btn")) {
        return;
    }

    const action = event.target.textContent.trim();

    // Only handle Important Points
    if (!action.includes("Important Points")) {
        return;
    }

    if (!uploadedStudyText.trim()) {

        alert("Please upload and read a study file first.");

        return;
    }

    const button = event.target;

    button.textContent = "🧠 MEMORA is thinking...";
    button.disabled = true;

    try {

        const response = await fetch(
            "/api/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    input: uploadedStudyText,

                    mode: "important"

                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            selectedFile.innerHTML += `
                <div class="ai-response">
                    <h3>⚠️ MEMORA ERROR</h3>
                    <p>${data.error || "Something went wrong."}</p>
                </div>
            `;

            button.textContent = "⭐ Important Points";
            button.disabled = false;

            return;
        }

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⭐ Important Points</h3>

                ${marked.parse(data.result)}
            </div>
        `;

        button.textContent = "✅ Important Points Ready";

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>

                <p>
                    MEMORA could not connect to the AI server.
                </p>
            </div>
        `;

        button.textContent = "⭐ Important Points";
        button.disabled = false;
    }

});
// ==========================================
// DOCUMENT AI — GENERATE QUIZ ❓
// ==========================================

document.addEventListener("click", async function (event) {

    if (!event.target.classList.contains("document-action-btn")) {
        return;
    }

    const action = event.target.textContent.trim();

    // Only handle Generate Quiz
    if (!action.includes("Generate Quiz")) {
        return;
    }

    if (!uploadedStudyText.trim()) {

        alert("Please upload and read a study file first.");

        return;
    }

    const button = event.target;

    button.textContent = "🧠 MEMORA is creating quiz...";
    button.disabled = true;

    try {

        const response = await fetch(
            "/api/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    input: uploadedStudyText,

                    mode: "quiz"

                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            selectedFile.innerHTML += `
                <div class="ai-response">
                    <h3>⚠️ MEMORA ERROR</h3>
                    <p>${data.error || "Something went wrong."}</p>
                </div>
            `;

            button.textContent = "❓ Generate Quiz";
            button.disabled = false;

            return;
        }

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>❓ MEMORA Quiz</h3>

                ${marked.parse(data.result)}
            </div>
        `;

        button.textContent = "✅ Quiz Generated";

    } catch (error) {

        console.error(error);

        selectedFile.innerHTML += `
            <div class="ai-response">
                <h3>⚠️ Connection Error</h3>

                <p>
                    MEMORA could not connect to the AI server.
                </p>
            </div>
        `;

        button.textContent = "❓ Generate Quiz";
        button.disabled = false;
    }

});

