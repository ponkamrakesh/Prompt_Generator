document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('transformForm');
    const input = document.getElementById('userInput');
    const charCount = document.getElementById('charCount');
    const btn = document.getElementById('transformBtn');
    const toggle = document.getElementById('toggleAdvanced');
    const advanced = document.getElementById('advancedContent');
    const checkboxes = document.querySelectorAll('.chip input');
    
    // Character count
    const updateCount = () => {
        charCount.textContent = `${input.value.length} / 500`;
    };
    input.addEventListener('input', updateCount);
    updateCount();
    
    // Max 3 styles
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            const checked = document.querySelectorAll('.chip input:checked');
            checkboxes.forEach(box => {
                if (!box.checked && checked.length >= 3) {
                    box.disabled = true;
                } else {
                    box.disabled = false;
                }
            });
        });
    });
    
    // Toggle advanced
    toggle?.addEventListener('click', () => {
        advanced.hidden = !advanced.hidden;
    });
    
    // Form submit
    form?.addEventListener('submit', () => {
        btn.querySelector('.ready').hidden = true;
        btn.querySelector('.loading').hidden = false;
        btn.disabled = true;
    });
    
    // Copy buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const text = btn.dataset.content;
            await navigator.clipboard.writeText(text);
            btn.textContent = '✓ Copied!';
            setTimeout(() => btn.textContent = '📋 Copy', 2000);
        });
    });
});
