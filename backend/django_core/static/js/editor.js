const CODE_TEMPLATES = {
    python: `# Write your solution here\ndef solve():\n    pass\n\nif __name__ == "__main__":\n    solve()\n`,
    java: `import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        // Write your code\n   }\n}\n`,
    cpp: `#include <bits/stdc++.h>\nusing namespace std;\nint main() {\n    // Write your code\n    return 0;\n}\n`,
    javascript: `// Write your code\nconst readline = require('readline');\nconst rl = readline.createInterface({input: process.stdin});\n`,
    go: `package main\nimport "fmt"\nfunc main() {\n    // Write your code\n    fmt.Println()\n}\n`,
};

function problemDetail() {
    return {
        language: 'python',
        running: false,
        submitting: false,
        verdict: null,
        verdictDisplay: '',
        runtime: null,
        errorMessage: null,
        submissions: [],
        editor: null,
        resizeHandler: null,
        
        init() {
            this.loadEditor();
            this.loadSubmissions();
        },
        
        loadEditor() {
            const self = this;
            require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' }});
            require(['vs/editor/editor.main'], function() {
                const container = document.getElementById('editor');
                if (!container) {
                    console.error('Editor container not found');
                    return;
                }
                
                self.editor = monaco.editor.create(container, {
                    value: CODE_TEMPLATES[self.language],
                    language: self.language,
                    theme: 'vs-dark',
                    // ❌ REMOVED: automaticLayout: true  (causes blinking)
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: 'JetBrains Mono, monospace',
                    scrollBeyondLastLine: false,
                    padding: { top: 16, bottom: 16 },
                    wordWrap: 'on',
                    scrollbar: {
                        verticalScrollbarSize: 8,
                        horizontalScrollbarSize: 8,
                    },
                });
                
                // Manual layout on container resize (debounced)
                let resizeTimeout;
                self.resizeHandler = () => {
                    clearTimeout(resizeTimeout);
                    resizeTimeout = setTimeout(() => {
                        if (self.editor) self.editor.layout();
                    }, 200);
                };
                
                // Listen to window resize
                window.addEventListener('resize', self.resizeHandler);
                
                // Use ResizeObserver for container-specific resizing
                if (window.ResizeObserver) {
                    const observer = new ResizeObserver(self.resizeHandler);
                    observer.observe(container);
                }
                
                // Initial layout after render
                setTimeout(() => {
                    if (self.editor) self.editor.layout();
                }, 100);
            });
        },
        
        onLanguageChange() {
            if (this.editor) {
                monaco.editor.setModelLanguage(this.editor.getModel(), this.language);
                this.editor.setValue(CODE_TEMPLATES[this.language] || '');
            }
        },
        
        resetCode() {
            if (this.editor) this.editor.setValue(CODE_TEMPLATES[this.language] || '');
        },
        
        getCode() { return this.editor ? this.editor.getValue() : ''; },
        
        runCode() { this.submit(true); },
        submitCode() { this.submit(false); },
        
        async submit(isSampleRun) {
            if (isSampleRun) this.running = true;
            else this.submitting = true;
            this.verdict = null;
            this.errorMessage = null;
            
            try {
                const token = localStorage.getItem('access_token');
                if (!token) { window.location.href = '/login/'; return; }
                
                const code = this.getCode();
                if (!code || code.trim().length < 10) {
                    alert('Code is too short.');
                    return;
                }
                
                const response = await fetch('/api/submissions/submit/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        problem: window.PROBLEM_DATA.id,
                        code: code,
                        language: this.language,
                        is_sample_run: isSampleRun,
                    }),
                });
                
                const data = await response.json();
                if (!response.ok) { alert('Submit failed: ' + JSON.stringify(data)); return; }
                await this.pollVerdict(data.id);
            } catch (err) {
                alert('Error: ' + err.message);
            } finally {
                this.running = false;
                this.submitting = false;
            }
        },
        
        async pollVerdict(submissionId) {
            const token = localStorage.getItem('access_token');
            for (let i = 0; i < 60; i++) {
                await new Promise(r => setTimeout(r, 1000));
                try {
                    const response = await fetch(`/api/submissions/${submissionId}/status/`, {
                        headers: {'Authorization': `Bearer ${token}`},
                    });
                    if (!response.ok) continue;
                    const data = await response.json();
                    if (data.verdict !== 'PENDING') {
                        this.verdict = data.verdict;
                        this.verdictDisplay = {
                            'AC': '✅ Accepted', 'WA': '❌ Wrong Answer',
                            'TLE': '⏰ Time Limit Exceeded', 'RE': '💥 Runtime Error',
                            'CE': '🔧 Compilation Error', 'SE': '⚠️ System Error',
                        }[data.verdict] || data.verdict;
                        this.runtime = data.runtime_ms;
                        this.errorMessage = data.error_message;
                        this.loadSubmissions();
                        return;
                    }
                } catch (err) { console.log('Poll error:', err); }
            }
        },
        
        async loadSubmissions() {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) return;
                const response = await fetch(`/api/submissions/?problem=${window.PROBLEM_DATA.slug}`, {
                    headers: {'Authorization': `Bearer ${token}`},
                });
                if (response.ok) {
                    const data = await response.json();
                    this.submissions = (data.results || data).slice(0, 5);
                }
            } catch (err) { console.log(err); }
        },
    };
}