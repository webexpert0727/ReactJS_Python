import React, { Component } from 'react';
import PropTypes from 'prop-types';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';


export default class LoginForm extends Component {

  static propTypes = {
    login: PropTypes.func.isRequired,
    errors: PropTypes.arrayOf(React.PropTypes.string).isRequired,
  }

  handleSubmit = (e) => {
    e.preventDefault();
    const username = this.username.value;
    const password = this.password.value;
    const rememberme = this.rememberme.checked;
    this.props.login({ username, password, rememberme });
  }

  render() {
    const errors = this.props.errors.map(error => (
      <div key={error}>
        <h4 style={{ textAlign: 'center', color: 'red' }}>{error}</h4>
      </div>
    ));

    return (
      <div className="container">
        <div className="row" style={{ marginTop: '40px' }}>
          <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">

            <h1 className="text-center">Admin Sign In</h1>

            <ReactCSSTransitionGroup
              component="div" transitionName="grow"
              transitionEnterTimeout={400}
              transitionLeaveTimeout={400}
            >
              {errors}
            </ReactCSSTransitionGroup>

            <div className="sign-in-wrapper">
              <form className="form-signin" onSubmit={this.handleSubmit}>
                <div className="form-group">
                  <label className="sr-only">Email address</label>
                  <input
                    className="form-control input-lg"
                    placeholder="Username"
                    required
                    ref={v => (this.username = v)}
                  />
                </div>
                <div className="form-group">
                  <label className="sr-only">Password</label>
                  <input
                    className="form-control input-lg"
                    placeholder="Password"
                    type="password"
                    required
                    ref={v => (this.password = v)}
                  />
                </div>
                <div className="text-center">
                  <input type="checkbox" ref={v => (this.rememberme = v)} /> Remember me
                </div>
                <button type="submit" className="btn btn-primary btn-lg btn-block">Sign in</button>
              </form>
            </div>

          </div>
        </div>
      </div>
    );
  }
}
