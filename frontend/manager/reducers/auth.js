export const types = Object.freeze({
  LOGIN_REQUEST: 'LOGIN_REQUEST',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT_REQUEST: 'LOGOUT_REQUEST',
  LOGOUT_SUCCESS: 'LOGOUT_SUCCESS',
  LOGOUT_FAILURE: 'LOGOUT_FAILURE',
  FETCH_USER_AUTHENTICATION: 'FETCH_USER_AUTHENTICATION',
});


export default function user(state = {}, action) {
  switch (action.type) {
    case types.LOGIN_SUCCESS:
      return { ...action.user };
    case types.LOGOUT_SUCCESS:
      return {};
    default:
      return state;
  }
}


export const actions = {
  login: payload => ({ type: types.LOGIN_REQUEST, payload }),
  logout: () => ({ type: types.LOGOUT_REQUEST }),
  fetchUserAuthentication: () => ({ type: types.FETCH_USER_AUTHENTICATION }),
};
