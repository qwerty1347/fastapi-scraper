class LLMConfig:
    MODELS = {
        'llama': {
            '3.1-8b-instant': {
                'model': 'llama-3.1-8b-instant',
                'temperature': 0.6,
                'timeout': 10,
                'max_tokens': 1000,
            },
            '3.3-70b-versatile': {
                'model': 'llama-3.3-70b-versatile',
                'temperature': 0.3,
                'timeout': 30,
                'max_tokens': 4000,
            },
        }
    }