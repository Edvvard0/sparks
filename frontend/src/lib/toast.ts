import toast from 'react-hot-toast';

export const showSuccess = (message: string) => {
  toast.success(message, {
    duration: 3000,
    position: 'top-center',
    style: {
      background: '#1F1F1F',
      color: '#FFFFFF',
      borderRadius: '12px',
      padding: '12px 16px',
    },
  });
};

export const showError = (message: string) => {
  toast.error(message, {
    duration: 4000,
    position: 'top-center',
    style: {
      background: '#EB454E',
      color: '#FFFFFF',
      borderRadius: '12px',
      padding: '12px 16px',
    },
  });
};

export const showLoading = (message: string) => {
  return toast.loading(message, {
    position: 'top-center',
    style: {
      background: '#1F1F1F',
      color: '#FFFFFF',
      borderRadius: '12px',
      padding: '12px 16px',
    },
  });
};

export default toast;

