import React from 'react';
import PropTypes from 'prop-types';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import { Link } from 'react-router-dom';

import { Auth } from '../utils';
import { ManagerRole } from '../constants';


const Navbar = ({ showNav, logout }) => (
  <nav id="navbar" className="navbar navbar-custom navbar-fixed-top">
    <div className="container-fluid">
      <div className="row">
        <div className="col-xs-12" style={{ paddingRight: '4%', paddingLeft: '4%' }}>

          <div className="navbar-header">
            <button
              type="button" className="navbar-toggle" data-toggle="collapse"
              data-target="#custom-collapse"
            >
              <span className="sr-only">Toggle navigation</span>
              <span className="icon-bar" />
              <span className="icon-bar" />
              <span className="icon-bar" />
            </button>
            <Link className="navbar-brand" to="/packing/">
              <img className="light-logo" width="100" alt="" src={STATIC + 'images/site-logo-light.png'} />
            </Link>
          </div>
          <div className="collapse navbar-collapse" id="custom-collapse">
            { showNav && (
              <ReactCSSTransitionGroup
                component="ul" className="nav navbar-nav navbar-right"
                transitionAppear transitionName="fade"
                transitionAppearTimeout={400} transitionEnterTimeout={400}
                transitionLeaveTimeout={400}
              >
                { Auth.role === ManagerRole.ADMIN &&
                  <li><Link to="/dashboard">Dashboard</Link></li>
                }
                <li><Link to="/packing">Packing</Link></li>
                <li><Link to="/customers">Customers</Link></li>
                { Auth.role === ManagerRole.ADMIN &&
                  <li><Link to="/marketing">Marketing</Link></li>
                }
                <li><Link to="/inventory">Inventory</Link></li>
                { Auth.role === ManagerRole.ADMIN &&
                  <li className="dropdown">
                    <a
                      role="button" className="dropdown-toggle" data-toggle="dropdown"
                      aria-haspopup="true" aria-expanded="false"
                    >
                      Analysis <span className="caret" />
                    </a>
                    <ul className="dropdown-menu" style={{ color: 'black' }}>
                      <li><Link to="/demand" style={{ lineHeight: '2.5' }}>Coffee Demand</Link></li>
                      <li><Link to="/segmentation" style={{ lineHeight: '2.5' }}>Customer Segmentation</Link></li>
                    </ul>
                  </li>
                }
                <li>
                  <Link to="/" onClick={logout} className="btn btn-nav bgcolor-warm" style={{ padding: '5px 15px' }}>
                    LOGOUT
                  </Link>
                </li>
              </ReactCSSTransitionGroup>
            )}
          </div>

        </div>
      </div>
    </div>
  </nav>
);


Navbar.propTypes = {
  showNav: PropTypes.bool.isRequired,
  logout: PropTypes.func.isRequired,
};


export default Navbar;
