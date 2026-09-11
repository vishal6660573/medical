    } catch (err) {
      const status = err?.response?.status
      const detail = err?.response?.data?.detail

      let errorMsg = "Sorry, I'm having trouble connecting. Please try again."

      if (detail === 'ollama_not_running') {
        errorMsg = "⚠️ MediBot's AI engine is not running.\n\nOpen a new terminal and run:\n**`ollama serve`**\n\nThen pull the model if not already done:\n**`ollama pull llama3.2`**\n\nThen try again."
      } else if (status === 429 || detail === 'rate_limit') {
        errorMsg = "⏳ Too many requests right now. Please wait **20–30 seconds** and try again."
      } else if (status === 504 || detail === 'timeout') {
        errorMsg = "⏳ Response is taking too long. The model may still be loading — please try again in a moment."
      } else if (status === 503 || detail === 'unavailable') {
        errorMsg = "MediBot is temporarily unavailable. Please check the backend is running."
      }

      setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }])