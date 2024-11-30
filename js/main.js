// This function will set text inside the input field
function setTextInsideInput() {
  const inputElement = document.getElementById('input-ai');  // Select the input field
  inputElement.value = "Duck it here...";  // Set the value inside the input
}

// Call the function to set text
setTextInsideInput();

// Function to toggle the chat popup visibility
function toggleChatPopup() {
  const chatPopup = document.getElementById("chat-popup");
  if (chatPopup.style.display === "none" || chatPopup.style.display === "") {
    chatPopup.style.display = "block";  // Show the popup
  } else {
    chatPopup.style.display = "none";  // Hide the popup
  }
}

// Function to close the chat popup
function closeChatPopup() {
  const chatPopup = document.getElementById("chat-popup");
  chatPopup.style.display = "none";  // Hide the popup
}

// Function to check model connection
async function checkModelConnection() {
  try {
    const response = await fetch("http://localhost:5001/check_connection", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    const data = await response.json();
    return data.status === "connected";
  } catch (error) {
    console.error("Model bağlantısı kontrol edilirken hata:", error);
    return false;
  }
}

// Function to search for a question
async function searchQuestion() {
  const questionInput = document.getElementById("input-ai");
  const resultElement = document.getElementById("result");
  const loadingElement = document.getElementById("loading");
  const responseTimeElement = document.getElementById("response-time");
   
  const question = questionInput.value.trim();
   
  // Validate question length
  if (question.split(" ").length < 2) {
    resultElement.innerHTML = "Lütfen daha fazla bilgi vererek soruyu tekrar sorunuz.";
    return;
  }
   
  // Show loading state
  loadingElement.style.display = "block";
  resultElement.innerHTML = "";
   
  // Check model connection first
  const isModelConnected = await checkModelConnection();
  if (!isModelConnected) {
    resultElement.innerHTML = "Model bağlantısı kurulamadı. Lütfen sistem yöneticinize başvurun.";
    loadingElement.style.display = "none";
    return;
  }
   
  try {
    const response = await fetch("http://localhost:5001/get_answer", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: question }),
    });
       
    if (!response.ok) {
      throw new Error("Ağ yanıtı yok.");
    }
       
    const data = await response.json();
       
    if (data.answer) {
      resultElement.innerHTML = data.answer;
      responseTimeElement.innerHTML = `Response time: ${data.response_time}`;
    } else {
      resultElement.innerHTML = "Cevap alınırken hata oluştu. Lütfen tekrar deneyin.";
    }
  } catch (error) {
    console.error("Yanıt getirilirken hata oluştu:", error);
    resultElement.innerHTML = "Model yanıt vermiyor. Lütfen daha sonra tekrar deneyin.";
  } finally {
    loadingElement.style.display = "none";
  }
}

// Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  // Chat toggle button
  const chatBotButton = document.getElementById("chat-bot");
  chatBotButton?.addEventListener("click", toggleChatPopup);
   
  // Close button
  const closeButton = document.querySelector(".close-btn-chatbot");
  closeButton?.addEventListener("click", closeChatPopup);
   
  // Input field
  const inputField = document.getElementById("input-ai");
  inputField?.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchQuestion();
    }
  });
   
  // Initial connection check
  checkModelConnection().then(isConnected => {
    if (!isConnected) {
      const resultElement = document.getElementById("result");
      resultElement.innerHTML = "Model bağlantısı kurulamadı. Lütfen sistem yöneticinize başvurun.";
    }
  });
});

// Presentation Page Filter
document.addEventListener("DOMContentLoaded", () => {
  const filterButtons = document.querySelectorAll(".filter-btn");
  const projectCards = document.querySelectorAll(".project-card");

  filterButtons.forEach(button => {
      button.addEventListener("click", () => {
          // Remove active class from all buttons
          filterButtons.forEach(btn => btn.classList.remove("active"));
          // Add active class to the clicked button
          button.classList.add("active");

          const filter = button.getAttribute("data-filter");

          // Show/Hide project cards based on filter
          projectCards.forEach(card => {
              if (filter === "all" || card.getAttribute("data-category") === filter) {
                  card.classList.add("show");
              } else {
                  card.classList.remove("show");
              }
          });
      });
  });

  // Initialize: show all cards on page load
  projectCards.forEach(card => card.classList.add("show"));
});
