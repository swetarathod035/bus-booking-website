/**
 * AnandBus — Main JavaScript
 * Global utilities and UI enhancements
 */

'use strict';

/* ─── Navbar scroll effect ─────────────────────────────────── */
window.addEventListener('scroll', function () {
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    if (window.scrollY > 30) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  }
});

/* ─── Auto-dismiss alerts ───────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  // Auto-close flash messages after 5 seconds
  document.querySelectorAll('.alert.fade.show').forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Initialize all Bootstrap tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // Initialize all Bootstrap popovers
  document.querySelectorAll('[data-bs-toggle="popover"]').forEach(function (el) {
    new bootstrap.Popover(el);
  });

  // Animate cards on scroll (Intersection Observer)
  const cards = document.querySelectorAll('.card');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('slide-up');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    cards.forEach(function (card) { observer.observe(card); });
  }
});

/* ─── CSRF helper ──────────────────────────────────────────── */
function getCsrfToken() {
  const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
  if (cookieMatch) return cookieMatch[1];
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

/* ─── Toast notification ────────────────────────────────────── */
function showToast(message, type = 'info', duration = 4000) {
  const icons = {
    success: 'fas fa-check-circle',
    danger:  'fas fa-exclamation-triangle',
    warning: 'fas fa-exclamation-circle',
    info:    'fas fa-info-circle',
  };
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} shadow position-fixed animate__animated animate__fadeInDown`;
  toast.style.cssText = 'top:80px;right:20px;z-index:9999;min-width:300px;max-width:440px;border-radius:14px;border:none;';
  toast.innerHTML = `<i class="${icons[type] || icons.info} me-2"></i>${message}
    <button type="button" class="btn-close ms-2 float-end" style="font-size:0.7rem;" onclick="this.parentElement.remove()"></button>`;
  document.body.appendChild(toast);
  setTimeout(function () {
    toast.classList.replace('animate__fadeInDown', 'animate__fadeOutRight');
    setTimeout(function () { toast.remove(); }, 600);
  }, duration);
}

/* ─── Format Indian currency ────────────────────────────────── */
function formatINR(amount) {
  return '₹' + parseFloat(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/* ─── Confirm action helper ─────────────────────────────────── */
function confirmAction(message, callback) {
  if (window.confirm(message)) callback();
}

/* ─── Print ticket ───────────────────────────────────────────── */
function printTicket() {
  window.print();
}

/* ─── Date helpers ───────────────────────────────────────────── */
function getTodayString() {
  return new Date().toISOString().split('T')[0];
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
}

/* ─── Seat selection helpers (global) ───────────────────────── */
window.AnandBus = {
  showToast,
  formatINR,
  confirmAction,
  getCsrfToken,
  getTodayString,
  formatDate,
};
