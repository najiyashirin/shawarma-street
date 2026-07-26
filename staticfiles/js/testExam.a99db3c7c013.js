const defaultQuizQuestions = [
    {
        category: "Grammar",
        question: "Choose the correct sentence.",
        options: ["She don't like coffee.", "She doesn't likes coffee.", "She doesn't like coffee.", "She not like coffee."],
        answer: 2
    },
    {
        category: "Vocabulary",
        question: "Which word is closest in meaning to “enormous”?",
        options: ["Tiny", "Huge", "Ordinary", "Quiet"],
        answer: 1
    },
    {
        category: "Grammar",
        question: "If I ___ more time, I would learn another language.",
        options: ["have", "had", "will have", "am having"],
        answer: 1
    },
    {
        category: "Everyday English",
        question: "Someone says, “Would you mind opening the window?” What is the best response?",
        options: ["Yes, I would mind.", "Not at all.", "The window is big.", "I don't know a window."],
        answer: 1
    },
    {
        category: "Reading",
        question: "Maya missed the bus, so she arrived late. Why was Maya late?",
        options: ["She woke up late.", "The bus was delayed.", "She missed the bus.", "She walked slowly."],
        answer: 2
    },
    {
        category: "Grammar",
        question: "By this time next year, they ___ the course.",
        options: ["complete", "completed", "will have completed", "are completing"],
        answer: 2
    },
    {
        category: "Vocabulary",
        question: "Choose the best word: The instructions were very ___, so everyone understood them.",
        options: ["clear", "rare", "rough", "narrow"],
        answer: 0
    },
    {
        category: "Grammar",
        question: "Which sentence uses the apostrophe correctly?",
        options: ["The dogs bowl is empty.", "The dog's bowl is empty.", "The dogs' is bowl empty.", "The dog's' bowl is empty."],
        answer: 1
    },
    {
        category: "Reading",
        question: "Although the task was difficult, Arun persisted until it was finished. What does “persisted” mean?",
        options: ["Gave up", "Asked for help", "Kept trying", "Changed the task"],
        answer: 2
    },
    {
        category: "Advanced English",
        question: "Choose the most natural sentence.",
        options: ["Rarely I have seen such a view.", "Rarely have I seen such a view.", "I have rarely saw such a view.", "Rarely I seen such a view."],
        answer: 1
    }
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
        level = "Advanced English";
        title = "Exceptional command of English!";
        message = "You handle complex grammar and vocabulary confidently. A personalized plan can sharpen advanced writing, fluency and exam technique.";
    } else if (score >= 7) {
        level = "Upper intermediate";
        title = "You have a strong foundation.";
        message = "You communicate well across most situations. Targeted work on nuance, advanced grammar and expression can help you reach the next level.";
    } else if (score >= 4) {
        level = "Developing intermediate";
        title = "A promising place to grow from.";
        message = "You understand everyday English and key grammar patterns. A structured curriculum can build accuracy, vocabulary and speaking confidence.";
    } else {
        level = "Foundation level";
        title = "Every confident speaker starts here.";
        message = "You are building the essentials. Focused support with core grammar, vocabulary and comprehension will help you make steady progress.";
    }

    questionScreen.hidden = true;
    resultScreen.hidden = false;
    document.getElementById("score-number").textContent = `${score}/10`;
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
    if (currentQuestion === quizQuestions.length - 1) {
        showResults();
    } else {
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
