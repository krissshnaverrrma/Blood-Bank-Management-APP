document.addEventListener("DOMContentLoaded", function () {
	const alerts = document.querySelectorAll(".alert");
	alerts.forEach((alert) => {
		setTimeout(() => {
			alert.classList.add("fade");
			setTimeout(() => alert.remove(), 500);
		}, 4000);
	});
	initAtomicIcon();
});
function initAtomicIcon() {
	const container = document.getElementById("atomic-container");
	if (container) {
		container.innerHTML = `<div class="static-blood-drop"></div>`;
	}
}
const modal = document.getElementById("about-modal");
function openModal() {
	modal.classList.add("active");
}
function closeModal(event) {
	if (event.target === modal || event.target.closest(".close-btn")) {
		modal.classList.remove("active");
	}
}
document.addEventListener("keydown", (e) => {
	if (e.key === "Escape" && modal.classList.contains("active")) {
		closeModal({ target: modal });
	}
});
function togglePassword(iconElement, fieldId) {
	const passwordField = document.getElementById(fieldId);

	if (passwordField.type === "password") {
		passwordField.type = "text";
		iconElement.classList.remove("fa-eye");
		iconElement.classList.add("fa-eye-slash");
	} else {
		passwordField.type = "password";
		iconElement.classList.remove("fa-eye-slash");
		iconElement.classList.add("fa-eye");
	}
}
