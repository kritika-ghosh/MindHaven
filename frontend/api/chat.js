const url = "https://api.groq.com/openai/v1/chat/completions";

module.exports = async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader(
        'Access-Control-Allow-Headers',
        'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization'
    );

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    if (req.method !== 'POST') {
        res.status(405).json({ error: 'Method not allowed' });
        return;
    }

    // Resolve Groq API Key
    let groqKey = req.headers.authorization ? req.headers.authorization.replace('Bearer ', '') : null;
    if (!groqKey || groqKey.startsWith('dummy') || groqKey.startsWith('gsk_YOUR') || groqKey === "") {
        groqKey = process.env.GROQ_KEY || process.env.GROQ_API_KEY || process.env.GROK_KEY;
    }

    if (!groqKey) {
        res.status(400).json({ error: 'Missing Groq API Key! Please configure GROQ_KEY in Vercel settings.' });
        return;
    }

    try {
        const body = req.body || {};
        // Map model name if needed
        let model = body.model || 'llama-3.3-70b-versatile';
        if (model === 'custom-qwen' || model === 'mindhaven-cbt') {
            model = 'llama-3.3-70b-versatile';
        }

        const payload = {
            model: model,
            messages: body.messages,
            temperature: body.temperature !== undefined ? body.temperature : 0.6,
            max_tokens: body.max_tokens !== undefined ? body.max_tokens : 400,
            stream: body.stream || false
        };

        const groqResponse = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${groqKey}`,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
            },
            body: JSON.stringify(payload)
        });

        if (!groqResponse.ok) {
            const errText = await groqResponse.text();
            res.status(groqResponse.status).json({ error: `Groq API returned: ${errText}` });
            return;
        }

        if (payload.stream) {
            res.setHeader('Content-Type', 'text/event-stream');
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('Connection', 'keep-alive');

            // Pipe stream
            const reader = groqResponse.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                res.write(decoder.decode(value));
            }
            res.end();
        } else {
            const data = await groqResponse.json();
            res.status(200).json(data);
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};
