/* Asistente interno: envía preguntas a /assistant/ask y pinta el diálogo. */
(function () {
  'use strict';
  var form = document.getElementById('chatForm');
  var input = document.getElementById('chatInput');
  var log = document.getElementById('chatLog');
  if (!form) return;

  function bubble(text, who, meta) {
    var message = document.createElement('div');
    message.className = 'chat-msg ' + who;
    var bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'chat-bubble';
    bubbleDiv.textContent = text;
    message.appendChild(bubbleDiv);
    if (meta) {
      var small = document.createElement('div');
      small.className = 'chat-meta muted';
      small.textContent = meta;
      message.appendChild(small);
    }
    log.appendChild(message);
    log.scrollTop = log.scrollHeight;
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var question = input.value.trim();
    if (!question) return;
    bubble(question, 'user');
    input.value = '';
    window.crmApi('/assistant/ask', {
      method: 'POST',
      body: JSON.stringify({question: question})
    }).then(function (res) {
      if (res.ok) {
        var data = res.data;
        bubble(data.answer, 'bot',
               'herramienta: ' + data.tool + ' · registrado en auditoría #' +
               data.logged_id);
      } else {
        bubble(res.data.message || 'No pude responder', 'bot');
      }
    });
  });
})();
