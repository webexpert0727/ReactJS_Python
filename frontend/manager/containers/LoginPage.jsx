import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';

import { LoginForm } from '../components';
import { actions } from '../reducers/auth';


class LoginPage extends Component {

  static propTypes = {
    user: PropTypes.object.isRequired, // eslint-disable-line
    errors: PropTypes.arrayOf(React.PropTypes.string).isRequired,
    login: PropTypes.func.isRequired,
    history: PropTypes.object.isRequired, // eslint-disable-line
    location:  PropTypes.object.isRequired, // eslint-disable-line
  }

  componentDidMount() {
    this.goNext(this.props);
  }

  componentWillReceiveProps(nextProps) {
    this.goNext(nextProps);
  }

  goNext({ user, history, location }) {
    if (user.isAuthenticated) {
      const nextUrl = typeof location.state !== 'undefined'
        ? location.state.from.pathname
        : user.defaultPath;
      history.push(nextUrl);
    }
  }

  render() {
    return <LoginForm login={this.props.login} errors={this.props.errors} />;
  }
}


const mapStateToProps = state => ({
  user: state.user,
  errors: state.errors,
});

const mapDispatchToProps = dispatch => ({
  login: payload => dispatch(actions.login(payload)),
});


export default withRouter(connect(
  mapStateToProps,
  mapDispatchToProps,
)(LoginPage));
