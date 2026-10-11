// Healthcare Data Management and Secure Patient Record System
// Client-side interactions & validation helpers

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 400);
        }, 6000);
    });

    // 2. Automatically uppercase Patient ID fields
    const patientIdInputs = document.querySelectorAll('#patient_id');
    patientIdInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    });

    // 3. Response time measurement helper for presentation demonstration
    window.measureServerLatency = async function() {
        const start = performance.now();
        try {
            const response = await fetch('/health');
            const data = await response.json();
            const duration = Math.round(performance.now() - start);
            console.log(`[Health Probe] Latency: ${duration}ms | Status: ${data.status}`);
            return { duration, data };
        } catch (err) {
            console.error('Health probe failed:', err);
            return null;
        }
    };
});
