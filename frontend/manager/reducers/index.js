import { combineReducers } from 'redux';

import user from './auth';
import { isLoadingReducer, errorsReducer } from './core';
import dashboard from './dashboard';


const rootReducer = combineReducers({
  user,
  errors: errorsReducer,
  isLoading: isLoadingReducer,
  dashboard,
});


export default rootReducer;
