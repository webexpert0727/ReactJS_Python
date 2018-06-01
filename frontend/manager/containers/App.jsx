import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';

import { Navbar, Footer, Loading } from '../components';
import { actions as authActions } from '../reducers/auth';


class App extends Component {

  static propTypes = {
    user: PropTypes.object.isRequired, // eslint-disable-line
    logout: PropTypes.func.isRequired,
    fetchUserAuthentication: PropTypes.func.isRequired,
    isLoading: PropTypes.bool.isRequired,
    children: PropTypes.node.isRequired,
  }

  componentDidMount() {
    const { user, fetchUserAuthentication } = this.props;
    if (!user.isAuthenticated) {
      fetchUserAuthentication();
    }
  }

  render() {
    const { user, logout } = this.props;
    return (
      <div>
        <Navbar showNav={!!user.isAuthenticated} logout={logout} />
        <div style={{ marginTop: '94px' }}>
          {this.props.isLoading
            ? <Loading />
            : this.props.children}
        </div>
        <Footer />
      </div>
    );
  }
}


const mapStateToProps = state => ({
  user: state.user,
  isLoading: state.isLoading,
});

const mapDispatchToProps = dispatch => ({
  fetchUserAuthentication: () => dispatch(authActions.fetchUserAuthentication()),
  logout: () => dispatch(authActions.logout()),
});


export default withRouter(connect(
  mapStateToProps,
  mapDispatchToProps,
)(App));
