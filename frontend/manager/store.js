import { createStore, applyMiddleware, compose } from 'redux';
import createSagaMiddleware from 'redux-saga';

import rootReducer from './reducers';
import rootSaga from './sagas';


const sagaMiddleware = createSagaMiddleware();
const middlewares = [sagaMiddleware];
let composeEnhancers = compose;

if (__DEV__) {
  // eslint-disable-next-line no-underscore-dangle
  composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
}


const configureStore = (preloadedState) => {
  const store = createStore(
    rootReducer,
    preloadedState,
    composeEnhancers(
      applyMiddleware(...middlewares),
    ),
  );

  if (__DEV__) {
    if (module.hot) {
      module.hot.accept('./reducers', () => {
        // eslint-disable-next-line global-require
        const nextRootReducer = require('./reducers').default;
        store.replaceReducer(nextRootReducer);
      });
    }
  }

  sagaMiddleware.run(rootSaga);

  return store;
};


export default configureStore;
