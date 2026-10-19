import { Role } from '@/shared/types/api.types';

const mapRoleToCodes = (roles: Role[]): string[] => {
  return roles.map((role) => role.code.toUpperCase());
};

const getHomeRouteByRole = (roles: Role[]) => {
  const roleCodes = mapRoleToCodes(roles);

  if (!roleCodes || roleCodes.length === 0) {
    return '/';
  }

  if (roleCodes.includes('ADMIN')) {
    return '/dashboard';
  }

  if (roleCodes.includes('USER')) {
    return '/';
  }

  return '/';
};

export const roleUtil = {
  mapRoleToCodes,
  getHomeRouteByRole,
};
