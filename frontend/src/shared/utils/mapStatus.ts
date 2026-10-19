const USER_STATUS = {
  ACTIVE: 'Hoạt động',
  UNVERIFIED: 'Chưa xác thực',
  LOCKED: 'Đã khóa',
  INACTIVE: 'Không hoạt động',
  PENDING: 'Đang chờ',
};

const USER_STATUS_COLOR = {
  ACTIVE:
    'text-green-500 border border-green-500 bg-green-100/50 dark:bg-green-900 dark:text-green-400 dark:border-green-400',
  INACTIVE:
    'text-gray-500 border border-gray-500 bg-gray-100/50 dark:bg-gray-900 dark:text-gray-400 dark:border-gray-400',
  PENDING:
    'text-yellow-500 border border-yellow-500 bg-yellow-100/50 dark:bg-yellow-900 dark:text-yellow-400 dark:border-yellow-400',
  UNVERIFIED:
    'text-yellow-500 border border-yellow-500 bg-yellow-100/50 dark:bg-yellow-900 dark:text-yellow-400 dark:border-yellow-400',
  LOCKED:
    'text-red-500 border border-red-500 bg-red-100/50 dark:bg-red-900 dark:text-red-400 dark:border-red-400',
};

const mapUserStatus = (status: string) => {
  status = status.toUpperCase();
  // check exist status in USER_STATUS
  if (USER_STATUS[status as keyof typeof USER_STATUS]) {
    return {
      label: USER_STATUS[status as keyof typeof USER_STATUS],
      color: USER_STATUS_COLOR[status as keyof typeof USER_STATUS],
    };
  }
  return {
    label: status,
    color: 'text-gray-500 border border-gray-500',
  };
};

export { mapUserStatus };
