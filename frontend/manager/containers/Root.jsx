import React from 'react';
import PropTypes from 'prop-types';
import { Provider } from 'react-redux';
import { AppContainer } from 'react-hot-loader';
import Routes from '../routes';


const Root = ({ store }) => (
  <AppContainer>
    <Provider store={store}>
      <Routes />
    </Provider>
  </AppContainer>
);


Root.propTypes = {
  store: PropTypes.object.isRequired, // eslint-disable-line
};


export default Root;
