const defaultQuizQuestions = [
    { category: "Mathematics", question: "What is 15% of 200?", options: ["15", "20", "30", "45"], answer: 2 },
    { category: "Science", question: "Which process allows plants to make their own food using sunlight?", options: ["Respiration", "Photosynthesis", "Digestion", "Evaporation"], answer: 1 },
    { category: "English", question: "Which word is closest in meaning to ‘enormous’?", options: ["Tiny", "Huge", "Ordinary", "Quiet"], answer: 1 },
    { category: "Social Studies", question: "What is the main purpose of a map key or legend?", options: ["To show the map's age", "To explain symbols on the map", "To measure rainfall", "To name every road"], answer: 1 },
    { category: "Mathematics", question: "Solve: 3(x + 4) = 21. What is x?", options: ["3", "5", "7", "9"], answer: 0 },
    { category: "Science", question: "Which state of matter has a fixed volume but takes the shape of its container?", options: ["Solid", "Liquid", "Gas", "Plasma"], answer: 1 },
    { category: "English", question: "Which sentence uses the apostrophe correctly?", options: ["The dogs bowl is empty.", "The dog's bowl is empty.", "The dogs' is bowl empty.", "The dog's' bowl is empty."], answer: 1 },
    { category: "Social Studies", question: "Which branch of government is generally responsible for making laws?", options: ["Legislative", "Executive", "Judicial", "Scientific"], answer: 0 },
    { category: "Mathematics", question: "A triangle has angles of 50°, 60°, and what is the third angle?", options: ["60°", "70°", "80°", "90°"], answer: 1 },
    { category: "General Knowledge", question: "Which planet is known as the Red Planet?", options: ["Venus", "Mars", "Jupiter", "Mercury"], answer: 1 }
];

const adminQuestionData = document.getElementById("admin-assessment-questions");
const uploadedQuestions = adminQuestionData ? JSON.parse(adminQuestionData.textContent) : [];
const quizQuestions = uploadedQuestions.length ? uploadedQuestions : defaultQuizQuestions;

document.querySelectorAll("[data-question-count]").forEach(element => {
    element.textContent = quizQuestions.length;
});

const modal = document.getElementById("quiz-modal");
const startScreen = document.getElementById("quiz-start");
const questionScreen = document.getElementById("quiz-questions");
const resultScreen = document.getElementById("quiz-result");
const answerList = document.getElementById("answer-list");
let currentQuestion = 0;
let answers = Array(quizQuestions.length).fill(null);

function openQuiz() {
    modal.hidden = false;
    document.body.classList.add("modal-open");
    document.getElementById("start-quiz").focus();
}

function closeQuiz() {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    document.getElementById("open-quiz").focus();
}

function resetQuiz() {
    currentQuestion = 0;
    answers = Array(quizQuestions.length).fill(null);
    startScreen.hidden = false;
    questionScreen.hidden = true;
    resultScreen.hidden = true;
}

function renderQuestion() {
    const item = quizQuestions[currentQuestion];
    document.getElementById("question-counter").textContent = `Question ${currentQuestion + 1} of ${quizQuestions.length}`;
    document.getElementById("quiz-category").textContent = item.category;
    document.getElementById("progress-bar").style.width = `${((currentQuestion + 1) / quizQuestions.length) * 100}%`;
    document.getElementById("question-text").textContent = item.question;
    document.getElementById("previous-question").disabled = currentQuestion === 0;
    document.getElementById("next-question").disabled = answers[currentQuestion] === null;
    document.getElementById("next-question").innerHTML = currentQuestion === quizQuestions.length - 1
        ? "See my results <span>→</span>"
        : "Next question <span>→</span>";

    answerList.innerHTML = "";
    item.options.forEach((option, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `answer-option${answers[currentQuestion] === index ? " selected" : ""}`;
        button.innerHTML = `<span class="answer-letter">${String.fromCharCode(65 + index)}</span><span>${option}</span>`;
        button.addEventListener("click", () => {
            answers[currentQuestion] = index;
            renderQuestion();
            document.getElementById("next-question").focus();
        });
        answerList.appendChild(button);
    });
}

function showResults() {
    const score = answers.reduce((total, answer, index) => total + (answer === quizQuestions[index].answer ? 1 : 0), 0);
    let level;
    let title;
    let message;

    if (score >= 9) {
        level = "Excellent all-rounder";
        title = "Exceptional subject knowledge!";
        message = "You show strong understanding across subjects. A personalized plan can deepen your knowledge and stretch your skills further.";
    } else if (score >= 7) {
        level = "Upper intermediate";
        title = "You have a strong foundation.";
        message = "You have a solid foundation across most subjects. Targeted support can help you strengthen the areas that will take you to the next level.";
    } else if (score >= 4) {
        level = "Developing intermediate";
        title = "A promising place to grow from.";
        message = "You have promising skills to build on. A structured learning plan can strengthen core concepts and build confidence in every subject.";
    } else {
        level = "Foundation level";
        title = "Every confident learner starts here.";
        message = "You are building the essentials. Focused support with core skills and concepts will help you make steady progress across subjects.";
    }

    questionScreen.hidden = true;
    resultScreen.hidden = false;
    document.getElementById("score-number").textContent = `${score}/${quizQuestions.length}`;
    document.getElementById("result-level").textContent = level;
    document.getElementById("result-title").textContent = title;
    document.getElementById("result-message").textContent = message;
    document.getElementById("result-breakdown").textContent =
        `You answered ${score} correctly and have ${quizQuestions.length - score} areas ready for focused improvement.`;
}

document.getElementById("open-quiz").addEventListener("click", openQuiz);
document.querySelectorAll("[data-close-quiz]").forEach(element => element.addEventListener("click", closeQuiz));
document.getElementById("start-quiz").addEventListener("click", () => {
    startScreen.hidden = true;
    questionScreen.hidden = false;
    renderQuestion();
});
document.getElementById("next-question").addEventListener("click", () => {
    if (answers[currentQuestion] === null) return;
    if (currentQuestion === quizQuestions.length - 1) showResults();
    else {
        currentQuestion += 1;
        renderQuestion();
    }
});
document.getElementById("previous-question").addEventListener("click", () => {
    if (currentQuestion > 0) {
        currentQuestion -= 1;
        renderQuestion();
    }
});
document.getElementById("retake-quiz").addEventListener("click", () => {
    resetQuiz();
    startScreen.hidden = true;
    questionScreen.hidden = false;
    renderQuestion();
});
document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !modal.hidden) closeQuiz();
});
