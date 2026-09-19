// ==========================================================
// MEMORA - COMPLETE SCRIPT
// PART 1
// ==========================================================


// ==========================================================
// START LEARNING
// ==========================================================

const startButton = document.querySelector(".start-btn");

if (startButton) {

    startButton.addEventListener("click", function () {

        const features = document.querySelector(".features");

        if (features) {

            features.scrollIntoView({
                behavior: "smooth"
            });

        }

    });

}


// ==========================================================
// STUDY MODES
// ==========================================================

const modeButtons = document.querySelectorAll(".mode-btn");

let selectedMode = "explain";

modeButtons.forEach(function (button) {

    button.addEventListener("click", function () {

        modeButtons.forEach(function (btn) {

            btn.classList.remove("active");

        });

        button.classList.add("active");

        selectedMode = button.dataset.mode;

    });

});


// ==========================================================
// AI TEXT CLEANER
// Removes ugly $ and LaTeX symbols from AI answers
// ==========================================================

function cleanAIText(text) {

    if (!text) {
        return "";
    }

    return String(text)

        // Remove $$ equation wrappers
        .replace(/\$\$([\s\S]*?)\$\$/g, "$1")

        // Remove $ equation wrappers
        .replace(/\$([^$\n]+)\$/g, "$1")

        // Remove \( \)
        .replace(/\\\(([\s\S]*?)\\\)/g, "$1")

        // Remove \[ \]
        .replace(/\\\[([\s\S]*?)\\\]/g, "$1")

        // Fractions
        .replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, "$1/$2")

        // Common math symbols
        .replace(/\\times/g, "×")
        .replace(/\\div/g, "÷")
        .replace(/\\cdot/g, "·")
        .replace(/\\pm/g, "±")
        .replace(/\\leq/g, "≤")
        .replace(/\\geq/g, "≥")
        .replace(/\\neq/g, "≠")

        // Square root
        .replace(/\\sqrt\{([^{}]+)\}/g, "√($1)")

        // Text command
        .replace(/\\text\{([^{}]*)\}/g, "$1")

        // Remove left/right commands
        .replace(/\\left/g, "")
        .replace(/\\right/g, "")

        // Remove remaining simple LaTeX commands
        .replace(/\\([a-zA-Z]+)/g, "$1")

        .trim();

}


// ==========================================================
// RENDER AI RESPONSE
// ==========================================================

function renderAIText(text) {

    const cleanedText = cleanAIText(text);

    if (typeof marked !== "undefined") {

        return marked.parse(cleanedText);

    }

    return cleanedText.replace(/\n/g, "<br>");

}


// ==========================================================
// MAIN AI GENERATOR
// ==========================================================

const generateButton =
    document.querySelector(".generate-btn");

const studyInput =
    document.querySelector("#studyInput");

const outputContent =
    document.querySelector(".output-content");


if (generateButton) {

    generateButton.addEventListener(
        "click",
        async function () {

            const userInput =
                studyInput.value.trim();


            // Empty input
            if (userInput === "") {

                outputContent.innerHTML = `

                    <div class="output-icon">
                        ⚠️
                    </div>

                    <h3>
                        Please enter something first
                    </h3>

                    <p>
                        Enter a topic, question, notes,
                        or your answer before generating.
                    </p>

                `;

                return;

            }


            // Loading
            outputContent.innerHTML = `

                <div class="output-icon">
                    ⏳
                </div>

                <h3>
                    MEMORA is thinking...
                </h3>

                <p>
                    Creating your learning result.
                </p>

            `;


            try {

                const response = await fetch(
                    "/api/generate",
                    {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            input: userInput,

                            mode: selectedMode

                        })

                    }
                );


                const data =
                    await response.json();


                // API ERROR
                if (!response.ok) {

                    if (response.status === 429) {

                        outputContent.innerHTML = `

                            <div class="output-icon">
                                ⏳
                            </div>

                            <h3>
                                AI LIMIT REACHED
                            </h3>

                            <p>
                                MEMORA has reached today's
                                AI request limit.
                            </p>

                            <p>
                                Please try again later.
                            </p>

                        `;

                    } else {

                        outputContent.innerHTML = `

                            <div class="output-icon">
                                ⚠️
                            </div>

                            <h3>
                                MEMORA ERROR
                            </h3>

                            <p>
                                ${
                                    data.error ||
                                    "Something went wrong."
                                }
                            </p>

                        `;

                    }

                    return;

                }


                // SUCCESS
                outputContent.innerHTML = `

                    <div class="output-icon">
                        🤖
                    </div>

                    <h3>
                        MEMORA'S RESPONSE
                    </h3>

                    <div class="ai-response">

                        ${renderAIText(data.result)}

                    </div>

                `;


            } catch (error) {

                console.error(
                    "MEMORA ERROR:",
                    error
                );


                outputContent.innerHTML = `

                    <div class="output-icon">
                        ⚠️
                    </div>

                    <h3>
                        MEMORA needs a moment
                    </h3>

                    <p>
                        We couldn't connect to the AI server.
                        Please check your connection and
                        try again.
                    </p>

                `;

            }

        }
    );

}


// ==========================================================
// STUDY PLANNER
// AI-POWERED PERSONALIZED TIME-TO-TIME PLAN
// ==========================================================

const plannerButton =
    document.querySelector(".planner-btn");

const examName =
    document.querySelector("#examName");

const examDate =
    document.querySelector("#examDate");

const subjects =
    document.querySelector("#subjects");

const studyHours =
    document.querySelector("#studyHours");

const plannerResult =
    document.querySelector(".planner-result");


// ==========================================================
// PLANNER ESCAPE
// ==========================================================

function plannerEscape(text) {

    return String(text)

        .replace(/&/g, "&amp;")

        .replace(/</g, "&lt;")

        .replace(/>/g, "&gt;")

        .replace(/"/g, "&quot;");

}


// ==========================================================
// PLANNER TIME
// ==========================================================

function plannerTime(minutes) {

    let hour =
        Math.floor(minutes / 60);

    let minute =
        minutes % 60;

    const period =
        hour >= 12 ? "PM" : "AM";


    if (hour > 12) {
        hour -= 12;
    }


    if (hour === 0) {
        hour = 12;
    }


    return `${hour}:${String(minute).padStart(
        2,
        "0"
    )} ${period}`;

}


// ==========================================================
// PLANNER MESSAGE
// ==========================================================

function showPlannerMessage(
    icon,
    title,
    message
) {

    plannerResult.innerHTML = `

        <div class="output-icon">
            ${icon}
        </div>

        <h3>
            ${title}
        </h3>

        <p>
            ${message}
        </p>

    `;

}


// ==========================================================
// STUDY PLANNER BUTTON
// ==========================================================

if (plannerButton) {

    plannerButton.addEventListener(
        "click",
        async function () {


            const name =
                examName.value.trim();


            const date =
                examDate.value;


            const subjectText =
                subjects.value.trim();


            const hours =
                Number(studyHours.value);


            // --------------------------------------------------
            // VALIDATION
            // --------------------------------------------------

            if (
                name === "" ||
                date === "" ||
                subjectText === "" ||
                hours <= 0
            ) {

                showPlannerMessage(

                    "⚠️",

                    "Please fill all details",

                    "Enter your exam name, exam date, subjects and daily study time."

                );

                return;

            }


            // --------------------------------------------------
            // DATE CALCULATION
            // --------------------------------------------------

            const today =
                new Date();

            today.setHours(
                0,
                0,
                0,
                0
            );


            const exam =
                new Date(date);

            exam.setHours(
                0,
                0,
                0,
                0
            );


            const difference =
                exam.getTime() -
                today.getTime();


            const daysLeft =
                Math.ceil(
                    difference /
                    (1000 * 60 * 60 * 24)
                );


            if (daysLeft < 1) {

                showPlannerMessage(

                    "⚠️",

                    "Choose a future exam date",

                    "Your exam date should be at least one day from today."

                );

                return;

            }


            // --------------------------------------------------
            // SUBJECTS
            // --------------------------------------------------

            const subjectList =
                subjectText

                    .split("\n")

                    .map(
                        subject =>
                            subject.trim()
                    )

                    .filter(
                        subject =>
                            subject !== ""
                    );


            if (subjectList.length === 0) {

                showPlannerMessage(

                    "⚠️",

                    "Please enter your subjects",

                    "Add at least one subject."

                );

                return;

            }


            // --------------------------------------------------
            // LOADING
            // --------------------------------------------------

            plannerResult.innerHTML = `

                <div class="output-icon">
                    🧠
                </div>

                <h3>
                    Creating your personalized plan...
                </h3>

                <p>
                    MEMORA is breaking your subjects
                    into smaller learning topics and
                    arranging them across your available days.
                </p>

            `;


            try {

                // --------------------------------------------------
                // SEND PLANNER DATA TO BACKEND
                // --------------------------------------------------

                const response =
                    await fetch(
                        "/api/generate",
                        {

                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body: JSON.stringify({

                                mode: "planner",

                                examName: name,

                                examDate: date,

                                subjects:
                                    subjectList.join("\n"),

                                studyHours: hours

                            })

                        }
                    );


                const data =
                    await response.json();


                // --------------------------------------------------
                // API ERROR
                // --------------------------------------------------

                if (!response.ok) {

                    throw new Error(

                        data.error ||
                        "Unable to create the study plan."

                    );

                }


                // ==================================================
                // IMPORTANT FIX
                // ==================================================
                //
                // The NEW backend already returns:
                //
                // data.result = {
                //     days: [...]
                // }
                //
                // Therefore we DO NOT use:
                //
                // .replace()
                //
                // and we DO NOT use:
                //
                // JSON.parse()
                //
                // ==================================================

                const plan =
                    data.result;


                if (
                    !plan ||
                    !plan.days ||
                    !Array.isArray(plan.days)
                ) {

                    console.error(
                        "Invalid planner response:",
                        plan
                    );

                    throw new Error(
                        "MEMORA could not create a valid study plan."
                    );

                }


                // --------------------------------------------------
                // CREATE TIME-TO-TIME SCHEDULE
                // --------------------------------------------------

                const totalMinutes =
                    Math.round(
                        hours * 60
                    );


                const studyBlock = 50;

                const breakBlock = 10;

                const recallBlock = 10;


                // 6:00 PM
                const startTime =
                    18 * 60;


                let allDaysHTML = "";


                plan.days.forEach(
                    (dayData, index) => {

                        const dayNumber =
                            index + 1;


                        let currentTime =
                            startTime;


                        let remainingStudyTime =
                            totalMinutes;


                        let dayHTML = `

                            <div class="planner-day">

                                <h3>
                                    📅 Day ${dayNumber}
                                </h3>

                        `;


                        const sessions =
                            Array.isArray(
                                dayData.sessions
                            )

                                ? dayData.sessions

                                : [];


                        // --------------------------------------------------
                        // STUDY SESSIONS
                        // --------------------------------------------------

                        sessions
                            .slice(0, 2)
                            .forEach(
                                (
                                    session,
                                    sessionIndex
                                ) => {


                                    if (
                                        remainingStudyTime <=
                                        recallBlock
                                    ) {

                                        return;

                                    }


                                    const sessionLength =
                                        Math.min(

                                            studyBlock,

                                            remainingStudyTime -
                                            recallBlock

                                        );


                                    const sessionStart =
                                        plannerTime(
                                            currentTime
                                        );


                                    const sessionEndMinutes =
                                        currentTime +
                                        sessionLength;


                                    const sessionEnd =
                                        plannerTime(
                                            sessionEndMinutes
                                        );


                                    const topic =
                                        plannerEscape(

                                            session.topic ||

                                            "Study topic"

                                        );


                                    const activity =
                                        plannerEscape(

                                            session.activity ||

                                            "Understand the concept and make short notes."

                                        );


                                    dayHTML += `

                                        <div class="planner-session">

                                            <strong>

                                                ⏰
                                                ${sessionStart}

                                                –

                                                ${sessionEnd}

                                            </strong>


                                            <p>

                                                🧠 Study:

                                                <strong>

                                                    ${topic}

                                                </strong>

                                            </p>


                                            <small>

                                                ${activity}

                                            </small>

                                        </div>

                                    `;


                                    currentTime =
                                        sessionEndMinutes;


                                    remainingStudyTime -=
                                        sessionLength;


                                    // BREAK AFTER SESSION 1
                                    if (
                                        sessionIndex === 0 &&
                                        remainingStudyTime >
                                        recallBlock
                                    ) {

                                        const breakStart =
                                            plannerTime(
                                                currentTime
                                            );


                                        currentTime +=
                                            breakBlock;


                                        const breakEnd =
                                            plannerTime(
                                                currentTime
                                            );


                                        dayHTML += `

                                            <div class="planner-break">

                                                ☕
                                                ${breakStart}

                                                –

                                                ${breakEnd}

                                                <br>

                                                <small>

                                                    Take a short break,
                                                    drink water and relax.

                                                </small>

                                            </div>

                                        `;


                                        remainingStudyTime -=
                                            breakBlock;

                                    }

                                }
                            );


                        // --------------------------------------------------
                        // EXTRA STUDY BLOCKS
                        // --------------------------------------------------

                        while (
                            remainingStudyTime >
                            recallBlock
                        ) {

                            const sessionLength =
                                Math.min(

                                    studyBlock,

                                    remainingStudyTime -
                                    recallBlock

                                );


                            const sessionStart =
                                plannerTime(
                                    currentTime
                                );


                            const sessionEndMinutes =
                                currentTime +
                                sessionLength;


                            const sessionEnd =
                                plannerTime(
                                    sessionEndMinutes
                                );


                            const fallbackTopic =
                                plannerEscape(

                                    subjectList[
                                        index %
                                        subjectList.length
                                    ]

                                );


                            dayHTML += `

                                <div class="planner-session">

                                    <strong>

                                        ⏰
                                        ${sessionStart}

                                        –

                                        ${sessionEnd}

                                    </strong>


                                    <p>

                                        🧠 Study:

                                        <strong>

                                            ${fallbackTopic}

                                        </strong>

                                    </p>


                                    <small>

                                        Practice questions,
                                        examples and revision.

                                    </small>

                                </div>

                            `;


                            currentTime =
                                sessionEndMinutes;


                            remainingStudyTime -=
                                sessionLength;


                            if (
                                remainingStudyTime >
                                recallBlock
                            ) {

                                const breakStart =
                                    plannerTime(
                                        currentTime
                                    );


                                currentTime +=
                                    breakBlock;


                                const breakEnd =
                                    plannerTime(
                                        currentTime
                                    );


                                dayHTML += `

                                    <div class="planner-break">

                                        ☕
                                        ${breakStart}

                                        –

                                        ${breakEnd}

                                        <br>

                                        <small>

                                            Take a short break,
                                            drink water and relax.

                                        </small>

                                    </div>

                                `;


                                remainingStudyTime -=
                                    breakBlock;

                            }

                        }


                        // --------------------------------------------------
                        // FINAL RECALL
                        // --------------------------------------------------

                        const recallStart =
                            plannerTime(
                                currentTime
                            );


                        currentTime +=
                            recallBlock;


                        const recallEnd =
                            plannerTime(
                                currentTime
                            );


                        const recallTask =
                            plannerEscape(

                                dayData.recall ||

                                "Close your notes and recall the main ideas without looking."

                            );


                        dayHTML += `

                            <div class="planner-session">

                                <strong>

                                    🔁
                                    ${recallStart}

                                    –

                                    ${recallEnd}

                                </strong>


                                <p>

                                    🧠 Final Recall

                                </p>


                                <small>

                                    ${recallTask}

                                </small>

                            </div>


                            </div>

                        `;


                        allDaysHTML +=
                            dayHTML;

                    }
                );


                // --------------------------------------------------
                // FINAL RESULT
                // --------------------------------------------------

                plannerResult.innerHTML = `

                    <div class="output-icon">

                        📚

                    </div>


                    <h3>

                        ${plannerEscape(name)}

                    </h3>


                    <p>

                        You have

                        <strong>

                            ${daysLeft} days

                        </strong>

                        remaining.

                    </p>


                    <p>

                        Daily study time:

                        <strong>

                            ${hours} hour(s)

                        </strong>

                    </p>


                    <hr>


                    <h3>

                        📅 Your AI-Powered Study Plan

                    </h3>


                    <p>

                        MEMORA has divided your subjects
                        into smaller learning topics and
                        arranged them into time-to-time
                        sessions.

                    </p>


                    ${allDaysHTML}


                    <hr>


                    <p>

                        💡
                        <strong>MEMORA Tip:</strong>

                        Follow the daily topics,
                        take your breaks and use
                        active recall instead of only
                        rereading your notes.

                    </p>

                `;


            } catch (error) {

                console.error(
                    "MEMORA PLANNER ERROR:",
                    error
                );


                plannerResult.innerHTML = `

                    <div class="output-icon">

                        ⚠️

                    </div>


                    <h3>

                        Couldn't create the study plan

                    </h3>


                    <p>

                        ${plannerEscape(

                            error.message ||

                            "Something went wrong. Please try again."

                        )}

                    </p>

                `;

            }

        }
    );

}
// ==========================================================
// MEMORA - COMPLETE SCRIPT
// PART 2
// ==========================================================


// ==========================================================
// POMODORO FOCUS MODE
// ==========================================================

let pomodoroInterval = null;

let pomodoroSeconds = 25 * 60;

let pomodoroRunning = false;

const pomodoroDisplay =
    document.querySelector("#pomodoroTimer") ||
    document.querySelector(".pomodoro-timer");

const pomodoroStart =
    document.querySelector("#pomodoroStart") ||
    document.querySelector(".pomodoro-start");

const pomodoroReset =
    document.querySelector("#pomodoroReset") ||
    document.querySelector(".pomodoro-reset");


function updatePomodoroDisplay() {

    if (!pomodoroDisplay) {
        return;
    }

    const minutes =
        Math.floor(
            pomodoroSeconds / 60
        );

    const seconds =
        pomodoroSeconds % 60;


    pomodoroDisplay.textContent =

        `${String(minutes).padStart(2, "0")}:${String(
            seconds
        ).padStart(2, "0")}`;

}


function startPomodoro() {

    if (pomodoroRunning) {
        return;
    }


    pomodoroRunning = true;


    if (pomodoroStart) {

        pomodoroStart.textContent =
            "⏸ Pause";

    }


    pomodoroInterval =
        setInterval(
            function () {

                if (pomodoroSeconds > 0) {

                    pomodoroSeconds--;

                    updatePomodoroDisplay();

                } else {

                    clearInterval(
                        pomodoroInterval
                    );

                    pomodoroInterval = null;

                    pomodoroRunning = false;


                    if (pomodoroStart) {

                        pomodoroStart.textContent =
                            "▶ Start";

                    }


                    alert(
                        "🎉 Focus session complete! Take a short break."
                    );

                }

            },
            1000
        );

}


function pausePomodoro() {

    if (!pomodoroRunning) {
        return;
    }


    clearInterval(
        pomodoroInterval
    );

    pomodoroInterval = null;

    pomodoroRunning = false;


    if (pomodoroStart) {

        pomodoroStart.textContent =
            "▶ Start";

    }

}


function resetPomodoro() {

    clearInterval(
        pomodoroInterval
    );

    pomodoroInterval = null;

    pomodoroRunning = false;

    pomodoroSeconds =
        25 * 60;


    updatePomodoroDisplay();


    if (pomodoroStart) {

        pomodoroStart.textContent =
            "▶ Start";

    }

}


if (pomodoroStart) {

    pomodoroStart.addEventListener(
        "click",
        function () {

            if (pomodoroRunning) {

                pausePomodoro();

            } else {

                startPomodoro();

            }

        }
    );

}


if (pomodoroReset) {

    pomodoroReset.addEventListener(
        "click",
        resetPomodoro
    );

}


updatePomodoroDisplay();

// ==========================================================
// QUICK STUDY
// Actually explains the entered topic
// ==========================================================

const quickStudyButton =
    document.querySelector(".quick-study-btn");

const quickTopic =
    document.querySelector("#quickTopic");

const quickResult =
    document.querySelector(".quick-result");

const quickTimeButtons =
    document.querySelectorAll(".quick-time");

let selectedQuickMinutes = 5;


// ==========================================================
// QUICK STUDY TIME BUTTONS
// ==========================================================

quickTimeButtons.forEach(function (button) {

    button.addEventListener("click", function () {

        quickTimeButtons.forEach(function (btn) {

            btn.classList.remove("active");

        });

        button.classList.add("active");

        selectedQuickMinutes =
            Number(button.dataset.minutes);

    });

});


// ==========================================================
// START QUICK STUDY
// ==========================================================

if (quickStudyButton) {

    quickStudyButton.addEventListener(
        "click",
        async function () {

            const topic =
                quickTopic
                    ? quickTopic.value.trim()
                    : "";


            // Empty topic validation
            if (!topic) {

                quickResult.innerHTML = `

                    <div class="output-icon">
                        ⚠️
                    </div>

                    <h3>
                        Enter a topic first
                    </h3>

                    <p>
                        Tell MEMORA what you want
                        to understand.
                    </p>

                `;

                return;

            }


            // Loading message
            quickResult.innerHTML = `

                <div class="output-icon">
                    🧠
                </div>

                <h3>
                    Explaining ${plannerEscape(topic)}...
                </h3>

                <p>
                    MEMORA is preparing a
                    ${selectedQuickMinutes}-minute
                    explanation.
                </p>

            `;


            try {

                // ==================================================
                // AI PROMPT
                // ==================================================

                const prompt = `

You are MEMORA, a friendly AI learning assistant.

The student wants to learn:

${topic}

They have ${selectedQuickMinutes} minutes.

IMPORTANT:

Actually TEACH the topic.

Do NOT create a generic timetable.

Use this structure:

1. What is the topic?
Explain it simply.

2. Core concept
Explain the most important idea.

3. Important points
Give the most important things the student
should remember.

4. Simple example
Give one easy example.

5. Quick practice
Give one small question or problem.

6. Memory trick
Give a simple way to remember the topic.

7. Final recap
Give 3 to 5 short revision points.

Adjust the amount of detail according to the
available ${selectedQuickMinutes} minutes.

Use simple student-friendly language.

Do not use LaTeX.

Do not use dollar signs for mathematical notation.

Do not create a study timetable.

Actually explain and teach the topic.

`;


                // ==================================================
                // SEND REQUEST TO FLASK
                // ==================================================

                const response =
                    await fetch(
                        "/api/generate",
                        {

                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                input: prompt,

                                mode: "quick-study"

                            })

                        }
                    );


                // ==================================================
                // READ RESPONSE
                // ==================================================

                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(

                        data.error ||
                        "Unable to create your quick study session."

                    );

                }


                // ==================================================
                // SHOW AI RESULT
                // ==================================================

                quickResult.innerHTML = `

                    <div class="output-icon">
                        ⚡
                    </div>

                    <h3>
                        Quick Study:
                        ${plannerEscape(topic)}
                    </h3>

                    <p>
                        <strong>
                            ${selectedQuickMinutes}-minute
                            learning session
                        </strong>
                    </p>

                    <div class="ai-response">

                        ${renderAIText(data.result)}

                    </div>

                `;


            } catch (error) {

                // ==================================================
                // ERROR HANDLING
                // ==================================================

                console.error(
                    "QUICK STUDY ERROR:",
                    error
                );


                quickResult.innerHTML = `

                    <div class="output-icon">
                        ⚠️
                    </div>

                    <h3>
                        Couldn't create your study session
                    </h3>

                    <p>
                        ${plannerEscape(
                            error.message ||
                            "Please try again."
                        )}
                    </p>

                `;

            }

        }
    );

}


// ==========================================================
// END QUICK STUDY
// ==========================================================
// ==========================================================
// TEACH IT BACK
// ==========================================================

const teachButton =
    document.querySelector(".teach-back-btn");

const teachInput =
    document.querySelector("#teachAnswer");

const teachResult =
    document.querySelector(".teach-result");


if (teachButton) {

    teachButton.addEventListener(
        "click",
        async function () {

            const answer =
                teachInput
                    ? teachInput.value.trim()
                    : "";


            if (!answer) {

                if (teachResult) {

                    teachResult.innerHTML = `

                        <div class="output-icon">
                            ⚠️
                        </div>

                        <h3>
                            Explain something first
                        </h3>

                        <p>
                            Write what you remember
                            and MEMORA will check it.
                        </p>

                    `;

                }

                return;

            }


            if (teachResult) {

                teachResult.innerHTML = `

                    <div class="output-icon">
                        🗣️
                    </div>

                    <h3>
                        Checking your explanation...
                    </h3>

                    <p>
                        MEMORA is looking for what
                        you understood correctly and
                        what you can improve.
                    </p>

                `;

            }


            try {

                const prompt = `

You are MEMORA, a supportive learning assistant.

The student is trying to teach a concept back to you.

Student explanation:

${answer}

Analyze it and provide:

1. What the student explained correctly
2. What is missing
3. What needs correction
4. A simple improved explanation
5. One short question for active recall

Be encouraging and educational.

Do not use LaTeX or dollar signs.

                `;


                const response =
                    await fetch(
                        "/api/generate",
                        {

                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({

                                input: prompt,

                                mode: "teach-back"

                            })

                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(

                        data.error ||
                        "Unable to check your explanation."

                    );

                }


                if (teachResult) {

                    teachResult.innerHTML = `

                        <div class="output-icon">
                            🗣️
                        </div>

                        <h3>
                            Your Teach-Back Review
                        </h3>

                        <div class="ai-response">

                            ${renderAIText(data.result)}

                        </div>

                    `;

                }


            } catch (error) {

                console.error(
                    "TEACH BACK ERROR:",
                    error
                );


                if (teachResult) {

                    teachResult.innerHTML = `

                        <div class="output-icon">
                            ⚠️
                        </div>

                        <h3>
                            Something went wrong
                        </h3>

                        <p>
                            ${plannerEscape(
                                error.message ||
                                "Please try again."
                            )}
                        </p>

                    `;

                }

            }

        }
    );

}


// ==========================================================
// UPLOAD & STUDY
// ==========================================================

let uploadedStudyText = "";

let uploadedFileName = "";


const studyFileInput =
    document.querySelector("#studyFile");

const uploadStudyButton =
    document.querySelector(".upload-study-btn");

const uploadResult =
    document.querySelector(".upload-result");


// ==========================================================
// FILE TYPE VALIDATION
// ==========================================================

function isAllowedStudyFile(file) {

    if (!file) {
        return false;
    }


    const allowedTypes = [

        "application/pdf",

        "text/plain",

        "application/vnd.ms-powerpoint",

        "application/vnd.openxmlformats-officedocument.presentationml.presentation",

        "image/png",

        "image/jpeg",

        "image/jpg",

        "image/webp"

    ];


    return allowedTypes.includes(
        file.type
    );

}


// ==========================================================
// FILE UPLOAD
// ==========================================================

if (uploadStudyButton) {

    uploadStudyButton.addEventListener(
        "click",
        async function () {

            const file =
                studyFileInput
                    ? studyFileInput.files[0]
                    : null;


            if (!file) {

                if (uploadResult) {

                    uploadResult.innerHTML = `

                        <div class="output-icon">
                            ⚠️
                        </div>

                        <h3>
                            Select a file first
                        </h3>

                        <p>
                            Upload a PDF, PPT, PPTX,
                            TXT or image.
                        </p>

                    `;

                }

                return;

            }


            if (!isAllowedStudyFile(file)) {

                if (uploadResult) {

                    uploadResult.innerHTML = `

                        <div class="output-icon">
                            ⚠️
                        </div>

                        <h3>
                            Unsupported file
                        </h3>

                        <p>
                            Please upload PDF, PPT,
                            PPTX, TXT or an image.
                        </p>

                    `;

                }

                return;

            }


            uploadedFileName =
                file.name;


            if (uploadResult) {

                uploadResult.innerHTML = `

                    <div class="output-icon">
                        ⏳
                    </div>

                    <h3>
                        Reading ${plannerEscape(file.name)}...
                    </h3>

                    <p>
                        MEMORA is extracting the
                        useful study content.
                    </p>

                `;

            }


            try {

                const formData =
                    new FormData();


                formData.append(
                    "file",
                    file
                );


                let endpoint = "";


                if (
                    file.type ===
                    "application/pdf"
                ) {

                    endpoint =
                        "/api/study-pdf";

                }

                else if (

                    file.type ===
                    "text/plain"

                ) {

                    endpoint =
                        "/api/study-txt";

                }

                else if (

                    file.type ===
                    "application/vnd.ms-powerpoint"

                    ||

                    file.type ===
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation"

                ) {

                    endpoint =
                        "/api/study-ppt";

                }

                else if (

                    file.type.startsWith(
                        "image/"
                    )

                ) {

                    endpoint =
                        "/api/study-image";

                }


                const response =
                    await fetch(
                        endpoint,
                        {

                            method: "POST",

                            body: formData

                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(

                        data.error ||
                        "Unable to read the file."

                    );

                }


                uploadedStudyText =
                    data.result || "";


                // --------------------------------------------------
                // IMAGE PREVIEW
                // --------------------------------------------------

                let imagePreview = "";


                if (
                    file.type.startsWith(
                        "image/"
                    )
                ) {

                    const imageURL =
                        URL.createObjectURL(
                            file
                        );


                    imagePreview = `

                        <div class="study-image-preview">

                            <img
                                src="${imageURL}"
                                alt="Uploaded study material"
                            >

                        </div>

                    `;

                }


                if (uploadResult) {

                    uploadResult.innerHTML = `

                        <div class="output-icon">
                            📚
                        </div>

                        <h3>
                            ${plannerEscape(file.name)}
                            is ready!
                        </h3>

                        ${imagePreview}


                        <div class="uploaded-study-text">

                            ${renderAIText(
                                uploadedStudyText
                            )}

                        </div>


                        <div class="document-actions">

                            <button
                                class="document-ai-btn"
                                data-action="summarize"
                            >
                                ✨ Summarize
                            </button>


                            <button
                                class="document-ai-btn"
                                data-action="explain"
                            >
                                🧠 Explain Simply
                            </button>


                            <button
                                class="document-ai-btn"
                                data-action="important"
                            >
                                ⭐ Important Points
                            </button>


                            <button
                                class="document-ai-btn"
                                data-action="quiz"
                            >
                                ❓ Generate Quiz
                            </button>

                        </div>


                        <div
                            class="document-ai-result"
                        ></div>

                    `;


                    attachDocumentButtons();

                }


            } catch (error) {

                console.error(
                    "UPLOAD ERROR:",
                    error
                );


                if (uploadResult) {

                    uploadResult.innerHTML = `

                        <div class="output-icon">
                            ⚠️
                        </div>

                        <h3>
                            Couldn't read the file
                        </h3>

                        <p>
                            ${plannerEscape(
                                error.message ||
                                "Please try again."
                            )}
                        </p>

                    `;

                }

            }

        }
    );

}


// ==========================================================
// DOCUMENT AI ACTIONS
// ==========================================================

function attachDocumentButtons() {

    const buttons =
        document.querySelectorAll(
            ".document-ai-btn"
        );


    buttons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                async function () {

                    if (!uploadedStudyText) {

                        return;

                    }


                    const action =
                        button.dataset.action;


                    const resultBox =
                        document.querySelector(
                            ".document-ai-result"
                        );


                    let instruction = "";


                    if (
                        action ===
                        "summarize"
                    ) {

                        instruction = `

Summarize the uploaded study material.

Give:
- Main idea
- Important concepts
- Key facts
- Short exam-focused summary

Keep it clear and easy to revise.

                        `;

                    }


                    else if (
                        action ===
                        "explain"
                    ) {

                        instruction = `

Explain the uploaded study material
in very simple student-friendly language.

Break difficult concepts into small parts.

Use simple examples where useful.

                        `;

                    }


                    else if (
                        action ===
                        "important"
                    ) {

                        instruction = `

Extract the most important points
from the uploaded study material.

Focus on:
- Definitions
- Important concepts
- Formulas
- Steps
- Exam-relevant facts

                        `;

                    }


                    else if (
                        action ===
                        "quiz"
                    ) {

                        instruction = `

Create a short quiz from the uploaded
study material.

Include:
- Multiple choice questions
- Concept-based questions
- Answers after the questions

                        `;

                    }


                    resultBox.innerHTML = `

                        <div class="output-icon">
                            ⏳
                        </div>

                        <h3>
                            MEMORA is working...
                        </h3>

                        <p>
                            Creating your
                            ${action} result.
                        </p>

                    `;


                    try {

                        const prompt = `

You are MEMORA, an AI-powered learning assistant.

The following content was uploaded by a student:

-------------------------

${uploadedStudyText}

-------------------------

${instruction}

Use ONLY the uploaded material
as the main source.

Do not invent unrelated information.

Do not use LaTeX or dollar signs.

Make the response readable and useful
for a student.

                        `;


                        const response =
                            await fetch(
                                "/api/generate",
                                {

                                    method: "POST",

                                    headers: {

                                        "Content-Type":
                                            "application/json"

                                    },

                                    body: JSON.stringify({

                                        input: prompt,

                                        mode:
                                            "document-" +
                                            action

                                    })

                                }
                            );


                        const data =
                            await response.json();


                        if (!response.ok) {

                            throw new Error(

                                data.error ||
                                "AI processing failed."

                            );

                        }


                        resultBox.innerHTML = `

                            <div class="output-icon">
                                🤖
                            </div>

                            <h3>
                                MEMORA's ${action}
                            </h3>

                            <div class="ai-response">

                                ${renderAIText(
                                    data.result
                                )}

                            </div>

                        `;


                    } catch (error) {

                        console.error(
                            "DOCUMENT AI ERROR:",
                            error
                        );


                        resultBox.innerHTML = `

                            <div class="output-icon">
                                ⚠️
                            </div>

                            <h3>
                                Couldn't process the document
                            </h3>

                            <p>
                                ${plannerEscape(
                                    error.message ||
                                    "Please try again."
                                )}
                            </p>

                        `;

                    }

                }
            );

        }
    );

}


// ==========================================================
// FILE INPUT PREVIEW
// ==========================================================

if (studyFileInput) {

    studyFileInput.addEventListener(
        "change",
        function () {

            const file =
                studyFileInput.files[0];


            if (!file) {
                return;
            }


            const fileName =
                document.querySelector(
                    ".selected-file-name"
                );


            if (fileName) {

                fileName.textContent =
                    file.name;

            }

        }
    );

}


// ==========================================================
// MOBILE MENU
// ==========================================================

const menuButton =
    document.querySelector(
        ".menu-toggle"
    );

const navigation =
    document.querySelector(
        ".nav-links"
    );


if (
    menuButton &&
    navigation
) {

    menuButton.addEventListener(
        "click",
        function () {

            navigation.classList.toggle(
                "active"
            );

        }
    );

}


// ==========================================================
// SMOOTH SCROLL FOR NAVIGATION
// ==========================================================

document
    .querySelectorAll(
        'a[href^="#"]'
    )
    .forEach(
        function (link) {

            link.addEventListener(
                "click",
                function (event) {

                    const targetID =
                        this.getAttribute(
                            "href"
                        );


                    if (
                        !targetID ||
                        targetID === "#"
                    ) {

                        return;

                    }


                    const target =
                        document.querySelector(
                            targetID
                        );


                    if (target) {

                        event.preventDefault();


                        target.scrollIntoView({

                            behavior:
                                "smooth",

                            block:
                                "start"

                        });

                    }

                }
            );

        }
    );


// ==========================================================
// PAGE LOAD
// ==========================================================

console.log(
    "🧠 MEMORA loaded successfully."
);

console.log(
    "Learn it. Understand it. Remember it."
);


// ==========================================================
// END OF MEMORA SCRIPT
// ==========================================================


