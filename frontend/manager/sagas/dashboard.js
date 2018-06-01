import { call, put, takeEvery } from 'redux-saga/effects';

import { ApiRequest } from '../utils';
import { types } from '../reducers/dashboard';


function* getReportCard(action) {
  const lastMonth = action.month.format('DD-MM-YYYY');
  const payload = { start_date: lastMonth, end_date: lastMonth };
  try {
    const { data: { reports } } = yield call(ApiRequest.get, 'getReportCard', payload);
    yield put({ type: types.REPORT_CARD_LOADED, report: reports[0] });
  } catch (e) {
    console.error(`checkReportCard: ${e}`);
  }
}


export default function* dashboardSaga() {
  yield [
    takeEvery(types.REPORT_CARD_REQUEST, getReportCard),
  ];
}
