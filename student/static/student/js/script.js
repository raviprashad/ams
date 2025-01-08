// script.js

document.getElementById('sendOTPBtn').addEventListener('click', function () {
    const email = document.getElementById('email').value;
    const otpSection = document.getElementById('otpSection');

    if (email) {
        const otp = Math.floor(100000 + Math.random() * 900000); // Generate 6-digit OTP
        console.log('Generated OTP:', otp);

        const templateParams = {
            to_email: email,
            otp: otp,
        };

        emailjs.send('YOUR_SERVICE_ID', 'YOUR_TEMPLATE_ID', templateParams)
            .then(response => {
                alert('OTP sent to your email!');
                localStorage.setItem('generatedOTP', otp); // Save OTP in local storage for verification
                otpSection.classList.remove('hidden'); // Show OTP input
            })
            .catch(error => {
                alert('Failed to send OTP. Check console for details.');
                console.error('EmailJS Error:', error);
            });
    } else {
        alert('Please enter a valid email address.');
    }
});

document.getElementById('verifyOTPBtn').addEventListener('click', function () {
    const enteredOTP = document.getElementById('otp').value;
    const storedOTP = localStorage.getItem('generatedOTP');

    if (enteredOTP === storedOTP) {
        alert('OTP verified successfully!');
        // Proceed with form submission or additional processing
    } else {
        alert('Invalid OTP. Please try again.');
    }
});
