$(document).ready(function () {
    const messageForm = $('#message-form');
    const userInput = $('#user-input');
    const messages = $('#messages');

    messageForm.on('submit', function (e) {
        e.preventDefault();
        const userText = userInput.val().trim();
        if (userText) {
            messages.append(`<div class="message user">${userText}</div>`);
            userInput.val('');
            scrollToBottom();

            $.ajax({
                url: '/ask',
                method: 'POST',
                data: { user_input: userText },
                success: function (data) {
                    const chatbotResponse = data.chatbot_response;
                    messages.append(`<div class="message chatbot">${chatbotResponse}</div>`);
                    scrollToBottom();
                },
            });
        }
    });

    function scrollToBottom() {
        messages.scrollTop(messages.prop('scrollHeight'));
    }
});
