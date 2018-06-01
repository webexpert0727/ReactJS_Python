import ApiRequest from './api';
import { ManagerRole } from '../constants';


export default class Auth {

  static role = {};
  static loggedIn = false;

  static async login(data) {
    try {
      const resp = await ApiRequest.post('login', data);
      const { data: { success, role } } = resp;
      Auth.role = ManagerRole[role.toUpperCase()];
      Auth.loggedIn = success;
      return { ...Auth.role, isAuthenticated: success };
    } catch (e) {
      throw new Error('Invalid Email/Password');
    }
  }

  static async logout() {
    try {
      await ApiRequest.get('logout');
      Auth.role = {};
      Auth.loggedIn = false;
    } catch (e) {
      throw e;
    }
  }

  static async fetchUserAuthentication() {
    try {
      const { data: { success, role } } = await ApiRequest.get('is_authenticated');
      Auth.role = ManagerRole[role.toUpperCase()];
      Auth.loggedIn = success;
      return { ...Auth.role, isAuthenticated: success };
    } catch (e) {
      throw e;
    }
  }

  static hasPerms(requireRole = {}) {
    const { accessLevel } = requireRole;
    return Auth.loggedIn && (!accessLevel || Auth.role.accessLevel >= accessLevel);
  }

}
