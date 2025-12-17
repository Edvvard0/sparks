import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ru from '../locales/ru.json';
import en from '../locales/en.json';
import es from '../locales/es.json';

// Определение языка из Telegram или localStorage
const getInitialLanguage = (): string => {
  // Пытаемся получить язык из Telegram
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    const telegramLang = window.Telegram.WebApp.initDataUnsafe?.user?.language_code;
    if (telegramLang) {
      // Маппинг языков Telegram на поддерживаемые
      const langMap: Record<string, string> = {
        'ru': 'ru',
        'en': 'en',
        'es': 'es',
        'uk': 'ru', // Украинский -> русский
        'be': 'ru', // Белорусский -> русский
        'kk': 'ru', // Казахский -> русский
      };
      const mappedLang = langMap[telegramLang.toLowerCase()];
      if (mappedLang) {
        localStorage.setItem('i18n_lng', mappedLang);
        return mappedLang;
      }
    }
  }

  // Пытаемся получить язык из localStorage
  const storedLang = localStorage.getItem('i18n_lng');
  if (storedLang && ['ru', 'en', 'es'].includes(storedLang)) {
    return storedLang;
  }

  // Пытаемся получить язык из профиля пользователя (если есть)
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      if (user?.language?.code && ['ru', 'en', 'es'].includes(user.language.code)) {
        localStorage.setItem('i18n_lng', user.language.code);
        return user.language.code;
      }
    }
  } catch (e) {
    // Игнорируем ошибки парсинга
  }

  // Fallback на английский
  return 'en';
};

const initialLanguage = getInitialLanguage();

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ru: { translation: ru },
      en: { translation: en },
      es: { translation: es },
    },
    lng: initialLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React уже экранирует
    },
  });

// Сохраняем язык при изменении
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('i18n_lng', lng);
});

export default i18n;
