import { useTranslation as useI18nTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import { useEffect } from 'react';

export const useTranslation = () => {
  const { language } = useApp();
  const { t, i18n: i18nInstance } = useI18nTranslation();

  // Синхронизация языка с контекстом
  useEffect(() => {
    if (language && i18nInstance.language !== language) {
      i18nInstance.changeLanguage(language);
    }
  }, [language, i18nInstance]);

  return { t };
};
