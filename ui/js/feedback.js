// js/feedback.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('feedbackForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const feedbackData = {
            name: document.getElementById('name')?.value.trim() || '',
            email: document.getElementById('email')?.value.trim() || '',
            organization: document.getElementById('organization')?.value.trim() || '',
            category: document.getElementById('category')?.value || '',
            message: document.getElementById('message')?.value.trim() || '',
            timestamp: firebase.database.ServerValue.TIMESTAMP
        };

        // Validation
        if (!feedbackData.name || !feedbackData.email || !feedbackData.message || !feedbackData.category) {
            alert('Please fill in all required fields.');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(feedbackData.email)) {
            alert('Please enter a valid email address.');
            return;
        }

        try {
            await firebase.database().ref('feedback').push(feedbackData);
            alert('Thank you for your feedback!');
            form.reset();
        } catch (error) {
            console.error('Submission error:', error);
            alert('Failed to submit. Please check your connection and try again.');
        }
    });
});