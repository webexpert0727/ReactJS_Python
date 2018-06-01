export const ManagerRole = Object.freeze({
  ADMIN: Object.freeze({
    role: 'admin',
    accessLevel: 2,
    defaultPath: '/dashboard',
  }),
  PACKER: Object.freeze({
    role: 'packer',
    accessLevel: 1,
    defaultPath: '/packing',
  }),
});


export const OrderType = Object.freeze({
  COFFEE: 'COFFEE',
  GEAR: 'GEAR',
  REDEM: 'REDEM',
});
