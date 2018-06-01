import React from 'react';
import { render as domRender } from 'react-dom';
import Root from './containers/Root';
import configureStore from './store';
import './styles/main.scss';  // only for backward compatibility

const appNode = document.getElementById('app');
const store = configureStore({});

const render = RootContainer => domRender(
  // eslint-disable-next-line react/jsx-filename-extension
  <RootContainer store={store} />,
  appNode
);

render(Root);


if (__DEV__) {
  if (module.hot) {
    module.hot.accept('./containers/Root', () => render(Root));
  }
}
