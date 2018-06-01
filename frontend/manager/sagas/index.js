import { fork } from 'redux-saga/effects';

import authSaga from './auth';
import dashboardSaga from './dashboard';


export default function* rootSaga() {
  yield [
    fork(authSaga),
    fork(dashboardSaga),
  ];
}
