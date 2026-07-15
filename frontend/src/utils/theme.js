export function applyTheme(hexColor) {
  if (!hexColor) {
    resetTheme();
    return;
  }
  
  const hex = hexColor.replace('#', '');
  let r, g, b;
  
  if (hex.length === 3) {
    r = parseInt(hex.charAt(0) + hex.charAt(0), 16);
    g = parseInt(hex.charAt(1) + hex.charAt(1), 16);
    b = parseInt(hex.charAt(2) + hex.charAt(2), 16);
  } else if (hex.length === 6) {
    r = parseInt(hex.substring(0, 2), 16);
    g = parseInt(hex.substring(2, 4), 16);
    b = parseInt(hex.substring(4, 6), 16);
  } else {
    return;
  }
  
  const root = document.documentElement;
  
  root.style.setProperty('--primary-500', hexColor);
  root.style.setProperty('--primary-400', `color-mix(in srgb, ${hexColor} 80%, white)`);
  root.style.setProperty('--primary-300', `color-mix(in srgb, ${hexColor} 60%, white)`);
  root.style.setProperty('--primary-600', `color-mix(in srgb, ${hexColor} 80%, black)`);
  root.style.setProperty('--primary-700', `color-mix(in srgb, ${hexColor} 60%, black)`);
  root.style.setProperty('--primary-800', `color-mix(in srgb, ${hexColor} 40%, black)`);
  root.style.setProperty('--primary-900', `color-mix(in srgb, ${hexColor} 20%, black)`);
  root.style.setProperty('--primary-rgb', `${r}, ${g}, ${b}`);
}

export function resetTheme() {
  const root = document.documentElement;
  root.style.removeProperty('--primary-500');
  root.style.removeProperty('--primary-400');
  root.style.removeProperty('--primary-300');
  root.style.removeProperty('--primary-600');
  root.style.removeProperty('--primary-700');
  root.style.removeProperty('--primary-800');
  root.style.removeProperty('--primary-900');
  root.style.removeProperty('--primary-rgb');
}

export function initTheme() {
  const isDark = localStorage.getItem('theme') === 'dark';
  if (isDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

export function toggleDarkTheme() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  return isDark;
}

export function isDarkMode() {
  return document.documentElement.classList.contains('dark');
}
