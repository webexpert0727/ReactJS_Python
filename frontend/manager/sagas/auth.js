import { call, put, takeEvery, takeLatest } from 'redux-saga/effects';

import { Auth } from '../utils';
import { types } from '../reducers/auth';


function* login(action) {
  try {
    const user = yield call(Auth.login, action.payload);
    yield put({ type: types.LOGIN_SUCCESS, user });
  } catch (e) {
    yield put({ type: types.LOGIN_FAILURE, errors: [e.message] });
  }
}

function* logout() {
  try {
    yield call(Auth.logout);
    yield put({ type: types.LOGOUT_SUCCESS });
  } catch (e) {
    yield put({ type: types.LOGOUT_FAILURE, errors: [e.message] });
  }
}

function* fetchUserAuthentication(action) {
  try {
    const user = yield call(Auth.fetchUserAuthentication, action.payload);
    yield put({ type: types.LOGIN_SUCCESS, user });
  } catch (e) {
    yield put({ type: types.LOGIN_FAILURE, errors: [] });
  }
}


export default function* authSaga() {
  yield [
    takeEvery(types.LOGIN_REQUEST, login),
    takeEvery(types.LOGOUT_REQUEST, logout),
    takeLatest(types.FETCH_USER_AUTHENTICATION, fetchUserAuthentication),
  ];
}
