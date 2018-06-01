import { types } from './auth';


export function errorsReducer(state, action) {
  switch (action.type) {
    case types.LOGIN_FAILURE:
    case types.LOGOUT_FAILURE:
      return [...action.errors];
    default:
      return [];
  }
}


export function isLoadingReducer(state, action) {
  switch (action.type) {
    case types.LOGIN_REQUEST:
    case types.LOGOUT_REQUEST:
      return true;
    default:
      return false;
  }
}
