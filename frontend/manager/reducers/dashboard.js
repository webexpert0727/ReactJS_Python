export const types = Object.freeze({
  REPORT_CARD_REQUEST: 'REPORT_CARD_REQUEST',
  REPORT_CARD_LOADED: 'REPORT_CARD_LOADED',
});


function reportCard(state = {}, action) {
  switch (action.type) {
    case types.REPORT_CARD_LOADED:
      return { ...action.report };
    default:
      return state;
  }
}


export default function dashboard(state = {}, action) {
  switch (action.type) {
    case types.REPORT_CARD_LOADED:
      return { ...state, reportCard: reportCard(undefined, action) };
    default:
      return state;
  }
}


export const actions = {
  getReportCard: month => ({ type: types.REPORT_CARD_REQUEST, month }),
};
