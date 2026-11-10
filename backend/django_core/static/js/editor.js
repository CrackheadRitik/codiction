/**
 * Codiction — Monaco Editor + Submit Handler
 * 
 * Features:
 * - Monaco editor with multi-language support
 * - Submit code with auto-refresh on 401
 * - Real-time verdict polling
 * - Recent submissions display
 * - Auto-layout without blinking
 */

// =====================================================
// LANGUAGE TEMPLATES
// =====================================================
const CODE_TEMPLATES = {
    python: `# Write your solution here
def solve():
    pass

if __name__ == "__main__":
    solve()
`,
    java: `import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        // Write your solution here
    }
}
`,
    cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    // Write your solution here
    return 0;
}
`,
    javascript: `// Write your solution here
const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.on('line', (line) => {
    // Process input
});
`,
    go: `package main

import "fmt"

func main() {
    // Write your solution here
    var input string
    fmt.Scan(&input)
    fmt.Println(input)
}
`,
};


// =====================================================
// PROBLEM DETAIL ALPINE COMPONENT
// =====================================================
function problemDetail() {
    return {
        language: 'python',
        running: false,
        submitting: false,
        verdict: null,
        verdictDisplay: '',
        runtime: null,
        memory: null,
        errorMessage: null,
        beatPercent: 85,
        submissions: [],
        editor: null,
        resizeHandler: null,
        
        // =====================================================
        // INITIALIZATION
        // =====================================================
        init() {
            this.loadEditor();
            this.loadSubmissions();
        },
        
        loadEditor() {
            const self = this;
            
            // Configure Monaco CDN
            require.config({ 
                paths: { 
                    'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' 
                }
            });
            
            require(['vs/editor/editor.main'], function() {
                const container = document.getElementById('editor');
                
                if (!container) {
                    console.error('❌ Editor container #editor not found');
                    return;
                }
                
                // Create Monaco editor
                self.editor = monaco.editor.create(container, {
                    value: CODE_TEMPLATES[self.language],
                    language: self.language,
                    theme: 'vs-dark',
                    // NOTE: automaticLayout removed to prevent blinking
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: 'JetBrains Mono, monospace',
                    scrollBeyondLastLine: false,
                    padding: { top: 16, bottom: 16 },
                    wordWrap: 'on',
                    tabSize: 4,
                    insertSpaces: true,
                    scrollbar: {
                        verticalScrollbarSize: 8,
                        horizontalScrollbarSize: 8,
                    },
                });
                
                // =====================================================
                // MANUAL RESIZE HANDLING (prevents blinking)
                // =====================================================
                let resizeTimeout;
                self.resizeHandler = () => {
                    clearTimeout(resizeTimeout);
                    resizeTimeout = setTimeout(() => {
                        if (self.editor) self.editor.layout();
                    }, 200);
                };
                
                // Window resize
                window.addEventListener('resize', self.resizeHandler);
                
                // Container resize (using ResizeObserver)
                if (window.ResizeObserver) {
                    const observer = new ResizeObserver(self.resizeHandler);
                    observer.observe(container);
                }
                
                // Initial layout after DOM settles
                setTimeout(() => {
                    if (self.editor) self.editor.layout();
                }, 100);
                
                console.log('✅ Monaco editor initialized');
            });
        },
        
        // =====================================================
        // LANGUAGE HANDLERS
        // =====================================================
        onLanguageChange() {
            if (!this.editor) return;
            
            monaco.editor.setModelLanguage(this.editor.getModel(), this.language);
            this.editor.setValue(CODE_TEMPLATES[this.language] || '');
        },
        
        resetCode() {
            if (this.editor) {
                this.editor.setValue(CODE_TEMPLATES[this.language] || '');
                this.verdict = null;
                this.errorMessage = null;
            }
        },
        
        getCode() {
            return this.editor ? this.editor.getValue() : '';
        },
        
        // =====================================================
        // SUBMIT HANDLERS
        // =====================================================
        runCode() {
            this.submit(true);
        },
        
        submitCode() {
            this.submit(false);
        },
        
        async submit(isSampleRun) {
            // Set loading state
            if (isSampleRun) {
                this.running = true;
            } else {
                this.submitting = true;
            }
            
            // Clear previous verdict
            this.verdict = null;
            this.verdictDisplay = '';
            this.runtime = null;
            this.memory = null;
            this.errorMessage = null;
            
            try {
                // Check auth
                const token = localStorage.getItem('access_token');
                if (!token) {
                    window.location.href = '/login/';
                    return;
                }
                
                // Validate code
                const code = this.getCode();
                if (!code || code.trim().length < 10) {
                    alert('Code is too short. Please write a solution (minimum 10 characters).');
                    return;
                }
                
                // Submit via API
                const response = await apiFetch('/api/submissions/submit/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        problem: window.PROBLEM_DATA.id,
                        code: code,
                        language: this.language,
                        is_sample_run: isSampleRun,
                    }),
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    alert('Submit failed: ' + JSON.stringify(data));
                    return;
                }
                
                // Poll for verdict
                await this.pollVerdict(data.id);
                
            } catch (err) {
                console.error('Submit error:', err);
                alert('Error: ' + err.message);
            } finally {
                this.running = false;
                this.submitting = false;
            }
        },
        
        // =====================================================
        // VERDICT POLLING
        // =====================================================
        async pollVerdict(submissionId) {
            const maxAttempts = 60;      // 60 attempts
            const intervalMs = 1000;      // 1 second each
            // Total: 60 seconds max
            
            for (let attempt = 0; attempt < maxAttempts; attempt++) {
                await new Promise(r => setTimeout(r, intervalMs));
                
                try {
                    const response = await apiFetch(`/api/submissions/${submissionId}/status/`);
                    
                    if (!response.ok) continue;
                    
                    const data = await response.json();
                    
                    // Verdict ready?
                    if (data.verdict !== 'PENDING') {
                        this.verdict = data.verdict;
                        this.runtime = data.runtime_ms;
                        this.memory = data.memory_mb;
                        this.errorMessage = data.error_message;
                        
                        // Display mapping
                        this.verdictDisplay = {
                            'AC': '✅ Accepted',
                            'WA': '❌ Wrong Answer',
                            'TLE': '⏰ Time Limit Exceeded',
                            'MLE': '💾 Memory Limit Exceeded',
                            'RE': '💥 Runtime Error',
                            'CE': '🔧 Compilation Error',
                            'SE': '⚠️ System Error',
                        }[data.verdict] || data.verdict;
                        
                        // Refresh submission list
                        this.loadSubmissions();
                        return;
                    }
                } catch (err) {
                    console.error('Poll error:', err);
                }
            }
            
            // Timeout
            this.verdict = 'SE';
            this.verdictDisplay = '⚠️ Judging Timeout';
            this.errorMessage = 'Taking too long. Check submission history later.';
        },
        
        // =====================================================
        // LOAD RECENT SUBMISSIONS
        // =====================================================
        async loadSubmissions() {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) return;
                
                const response = await apiFetch(
                    `/api/submissions/?problem=${window.PROBLEM_DATA.slug}&page_size=5`
                );
                
                if (response.ok) {
                    const data = await response.json();
                    this.submissions = (data.results || data).slice(0, 5);
                }
            } catch (err) {
                console.error('Load submissions error:', err);
            }
        },
    };
}