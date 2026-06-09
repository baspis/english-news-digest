function speakWord(btn) {
  const word = btn.dataset.word;
  if (!word || !window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(word);
  u.lang = 'en-US';
  u.rate = 0.9;
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

function collapseAllDeepDives() {
  document.querySelectorAll('.deep-dive[open]').forEach((el) => {
    el.open = false;
  });
}

function currentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

function updateThemeToggleLabel() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const dark = currentTheme() === 'dark';
  btn.textContent = dark ? '☀️ Light' : '🌙 Dark';
  btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('end-theme', theme);
  updateThemeToggleLabel();
}

function toggleTheme() {
  setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', toggleTheme);
    updateThemeToggleLabel();
  }
});
