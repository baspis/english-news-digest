let cachedEnglishVoice = null;

function isEnglishVoice(voice) {
  return /^en(-|$)/i.test(voice.lang || '');
}

function englishVoiceScore(voice) {
  const name = (voice.name || '').toLowerCase();
  const uri = (voice.voiceURI || '').toLowerCase();
  const blob = name + ' ' + uri;
  let score = 0;

  if (/premium/.test(blob)) score += 100;
  else if (/enhanced/.test(blob)) score += 80;

  const lang = (voice.lang || '').toLowerCase();
  if (lang === 'en-us') score += 30;
  else if (lang.startsWith('en')) score += 15;

  const preferred = [
    'ava', 'allison', 'nathan', 'zoe', 'samantha', 'alex', 'susan', 'karen',
  ];
  for (let i = 0; i < preferred.length; i += 1) {
    if (name.includes(preferred[i])) {
      score += 50 - i * 3;
      break;
    }
  }

  if (voice.localService) score += 5;
  if (/apple|com\.apple/.test(uri)) score += 10;
  if (/compact|eloquence/.test(blob) && !/premium|enhanced/.test(blob)) score -= 20;

  return score;
}

function pickBestEnglishVoice(voices) {
  const english = voices.filter(isEnglishVoice);
  if (!english.length) return null;
  return english.reduce((best, voice) => (
    englishVoiceScore(voice) > englishVoiceScore(best) ? voice : best
  ));
}

function getBestEnglishVoice() {
  if (!window.speechSynthesis) return null;
  if (cachedEnglishVoice) return cachedEnglishVoice;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;
  cachedEnglishVoice = pickBestEnglishVoice(voices);
  return cachedEnglishVoice;
}

function primeEnglishVoice() {
  if (!window.speechSynthesis) return;
  getBestEnglishVoice();
  speechSynthesis.addEventListener('voiceschanged', () => {
    cachedEnglishVoice = null;
    getBestEnglishVoice();
  });
}

function speakText(btn) {
  const text = btn.dataset.text || btn.dataset.word;
  if (!text || !window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  const voice = getBestEnglishVoice();
  if (voice) {
    u.voice = voice;
    u.lang = voice.lang;
  } else {
    u.lang = 'en-US';
  }
  u.rate = 0.9;
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

function speakWord(btn) {
  speakText(btn);
}

primeEnglishVoice();

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
