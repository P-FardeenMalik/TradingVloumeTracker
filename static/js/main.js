// Add smooth scrolling to all links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Add loading state to buttons
document.querySelectorAll('button[type="submit"]').forEach(button => {
    button.addEventListener('click', function() {
        if (this.form.checkValidity()) {
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            this.disabled = true;
        }
    });
});

// Password strength meter
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirm_password');

if (passwordInput && confirmPasswordInput) {
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        let strength = 0;
        
        if (password.length >= 8) strength++;
        if (password.match(/[a-z]+/)) strength++;
        if (password.match(/[A-Z]+/)) strength++;
        if (password.match(/[0-9]+/)) strength++;
        if (password.match(/[^a-zA-Z0-9]+/)) strength++;
        
        const strengthMeter = document.createElement('div');
        strengthMeter.className = 'progress mt-2';
        strengthMeter.innerHTML = `
            <div class="progress-bar" role="progressbar" style="width: ${strength * 20}%"></div>
        `;
        
        const existingMeter = this.parentElement.querySelector('.progress');
        if (existingMeter) {
            existingMeter.remove();
        }
        
        this.parentElement.appendChild(strengthMeter);
        
        const progressBar = strengthMeter.querySelector('.progress-bar');
        if (strength <= 2) {
            progressBar.className = 'progress-bar bg-danger';
        } else if (strength <= 3) {
            progressBar.className = 'progress-bar bg-warning';
        } else {
            progressBar.className = 'progress-bar bg-success';
        }
    });
    
    confirmPasswordInput.addEventListener('input', function() {
        if (this.value !== passwordInput.value) {
            this.setCustomValidity('Passwords do not match');
        } else {
            this.setCustomValidity('');
        }
    });
}

// Auto-hide alerts after 5 seconds
document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}); 