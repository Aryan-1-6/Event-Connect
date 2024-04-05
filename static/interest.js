// Function to handle showing interest
function showInterest(packageId) {
    // Prepare data to send in the AJAX request
    const requestData = {
        packageId: packageId
    };

    // Send AJAX request to backend
    fetch('/show_interest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken() // Include CSRF token
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Your interest has been sent to the organizer.');
        } else {
            alert('Failed to send interest. Please try again later.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again later.');
    });
}

// Function to get CSRF token from meta tag
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    } else {
        console.error('CSRF meta tag not found');
        return '';
    }
}
